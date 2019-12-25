# Copyright (c) 2019 Alexander Todorov <atodorov@MrSenko.com>
#
# Licensed under the GPL 3.0: https://www.gnu.org/licenses/gpl-3.0.txt
#

from django_tenants.utils import tenant_context
from social_django.models import UserSocialAuth


from tcms.management.models import Classification
from tcms.management.models import Product
from tcms.management.models import Version

from tcms_tenants.models import Tenant
from tcms_github_app.models import AppInstallation


def find_user_from_sender(sender_id):
    """
        Returns a User object from the DB which matches the person who
        triggered this event on the GitHub side by matching GitHub UID
        against UserSocialAuth.uid.
    """
    social_user = UserSocialAuth.objects.filter(uid=sender_id).first()
    if not social_user:
        return None

    return social_user.user


def find_tenant(data):
    """
        Return a Tenant for this installation or None
        if installation doesn't exist/isn't configured yet.
    """
    app_inst = AppInstallation.objects.filter(
        installation=data.payload['installation']['id']
    ).first()

    if not app_inst:
        return None

    return Tenant.objects.filter(pk=app_inst.tenant_pk).first()


def _product_from_repo(repo_data):
    # skip forks
    if repo_data.get('fork', False):
        return None

    name = repo_data['full_name']

    product = Product.objects.filter(name=name).first()

    # in case product already exists we don't want to create another one b/c
    # the name field is unique. When using .get_or_create() on all 3 fields
    # (name, description, classification) a new object will be created unless the 3 match!
    # this leads to "duplicate key value violates unique constraint" error:
    # https://sentry.io/organizations/open-technologies-bulgaria-ltd/issues/1405498335/
    if product:
        return product

    description = repo_data.get('description', '')
    classification, _created = Classification.objects.get_or_create(name='Imported from GitHub')
    return Product.objects.create(
        name=name,
        description=description,
        classification=classification,
    )


def create_product_from_repository(data):
    tenant = find_tenant(data)

    # can't handle requests from unconfigured installation
    if not tenant:
        return

    with tenant_context(tenant):
        _product_from_repo(data.payload['repository'])


def create_installation(data):
    """
        Records an AppInstallation object which will be used to
        access tenant & syncronize repositories if possible
    """
    tenant = None
    tenant_pk = None

    user = find_user_from_sender(data.sender)
    # either hadn't logged in before, e.g. install webhook
    # payload came in before the user completed their login or
    # GitHub admin isn't in Kiwi TCMS
    if user is None:
        pass
    elif user.tenant_set.count() == 0:
        # user has access only to public.tenant, e.g. trying out the demo
        tenant = Tenant.objects.get(schema_name='public')
        tenant_pk = tenant.pk
    elif user.tenant_set.count() == 1:
        # user has access to only 1 private tenant, work with it
        tenant = user.tenant_set.first()
        tenant_pk = tenant.pk

    AppInstallation.objects.create(
        installation=data.payload['installation']['id'],
        sender=data.sender,
        tenant_pk=tenant_pk,
    )

    if tenant and tenant_pk:
        with tenant_context(tenant):
            for repository in data.payload['repositories']:
                _product_from_repo(repository)


def create_version_from_tag(data):
    tenant = find_tenant(data)

    # can't handle requests from unconfigured installation
    if not tenant:
        return

    with tenant_context(tenant):
        product = _product_from_repo(data.payload['repository'])
        if not product:
            return

        Version.objects.create(
            value=data.payload['ref'],
            product=product
        )
