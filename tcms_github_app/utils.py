# Copyright (c) 2019-2020 Alexander Todorov <atodorov@MrSenko.com>
#
# Licensed under the GPL 3.0: https://www.gnu.org/licenses/gpl-3.0.txt
#

from django.conf import settings
from django.contrib import messages
from django.core.cache import cache
from django.utils.translation import gettext_lazy as _

import github
from django_tenants.utils import tenant_context
from social_django.models import UserSocialAuth

from tcms.management.models import Classification
from tcms.management.models import Product
from tcms.management.models import Version
from tcms.testcases.models import BugSystem

from tcms_tenants.models import Tenant
from tcms_github_app.models import AppInstallation


RECORD_SKIPPED = 0
RECORD_EXISTS = 10
RECORD_CREATED = 20


class KiwiTCMSGithub(github.Github):
    def __init__(  # pylint: disable=too-many-arguments
            self,
            login_or_token=None,
            password=None,
            jwt=None,
            base_url=github.MainClass.DEFAULT_BASE_URL,
            timeout=github.MainClass.DEFAULT_TIMEOUT,
            client_id=None,
            client_secret=None,
            user_agent="PyGithub/Python",
            per_page=github.MainClass.DEFAULT_PER_PAGE,
            verify=True,
            retry=None,
    ):
        super().__init__(
            login_or_token,
            password,
            jwt,
            base_url,
            timeout,
            client_id,
            client_secret,
            user_agent,
            per_page,
            verify,
            retry,
        )

        # create our own b/c we can't access self.__requester from parent class
        self.requester = github.Requester.Requester(
            login_or_token,
            password,
            jwt,
            base_url,
            timeout,
            client_id,
            client_secret,
            user_agent,
            per_page,
            verify,
            retry,
        )

    def get_installation(self, inst_id):
        return github.Installation.Installation(
            self.requester, headers={}, attributes={"id": inst_id}, completed=True
        )


def find_token_from_app_inst(gh_app, installation):
    """
        Find an installation access token for this app:
        https://docs.github.com/en/rest/reference/apps#create-an-installation-access-token-for-an-app

        and cache it for 50 mins!
    """
    cache_key = "token-for-%d" % installation.installation

    token = cache.get(cache_key)
    if not token:
        token = gh_app.get_access_token(installation.installation)
        token = token.token
        # token expires after 1 hr so cache it for 50 mins
        cache.set(cache_key, token, 3000)

    return token


def github_rpc_from_inst(installation):
    gh_app = github.GithubIntegration(settings.KIWI_GITHUB_APP_ID,
                                      settings.KIWI_GITHUB_APP_PRIVATE_KEY)

    token = find_token_from_app_inst(gh_app, installation)
    return KiwiTCMSGithub(token)


def github_installation_from_inst(app_inst):
    """
        Return a github.Installation.Installation object
        which holds information about all repositories we have access to!
    """
    rpc = github_rpc_from_inst(app_inst)
    return rpc.get_installation(app_inst.installation)


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
        return (tenant, app_inst)

        Return a Tenant for this installation or None
        if installation doesn't exist/isn't configured yet.
    """
    app_inst = AppInstallation.objects.filter(
        installation=data.payload['installation']['id']
    ).first()

    if not app_inst:
        return None, None

    tenant = Tenant.objects.filter(pk=app_inst.tenant_pk).first()

    return tenant, app_inst


def find_installations(request):
    """
        Find App installation for the current tenant + user
    """
    # find AppInstallation on the current tenant
    installations = AppInstallation.objects.filter(tenant_pk=request.tenant.pk)

    # if there are more than 1 (usually on public) then try to find the installation
    # performed by the current user, e.g. on their own account
    if installations.count() > 1:
        social_user = request.user.social_auth.first()
        if social_user:
            installations = installations.filter(sender=social_user.uid)

    return installations


def _product_from_repo(repo_object):
    """
        repo_object is a github.Repository.Repository object

        Returns (Product, int). The second element indicates status.
    """
    # skip forks
    if repo_object.fork:
        return None, RECORD_SKIPPED

    name = repo_object.full_name

    product = Product.objects.filter(name=name).first()

    # in case product already exists we don't want to create another one b/c
    # the name field is unique. When using .get_or_create() on all 3 fields
    # (name, description, classification) a new object will be created unless the 3 match!
    # this leads to "duplicate key value violates unique constraint" error:
    # https://sentry.io/organizations/open-technologies-bulgaria-ltd/issues/1405498335/
    if product:
        return product, RECORD_EXISTS

    description = repo_object.description
    if not description:
        description = 'GitHub repository'

    classification, _created = Classification.objects.get_or_create(name='Imported from GitHub')
    return Product.objects.create(
        name=name,
        description=description,
        classification=classification,
    ), RECORD_CREATED


def _bugtracker_from_repo(repo_object):
    """
        repo_object is a github.Repository.Repository object

        Returns (Product, int). The second element indicates status.
    """
    # skip forks
    if repo_object.fork:
        return None, RECORD_SKIPPED

    name = repo_object.full_name
    bug_system, created = BugSystem.objects.get_or_create(
        name='GitHub Issues for %s' % name,
        tracker_type='tcms_github_app.issues.Integration',
        base_url=repo_object.html_url,
    )

    db_status = RECORD_EXISTS
    if created:
        db_status = RECORD_CREATED

    return bug_system, db_status


def create_product_from_repository(data):
    tenant, installation = find_tenant(data)

    # can't handle requests from unconfigured installation
    if not tenant:
        return

    with tenant_context(tenant):
        rpc = github_rpc_from_inst(installation)
        repo_object = rpc.get_repo(data.payload['repository']['full_name'])

        _product_from_repo(repo_object)
        _bugtracker_from_repo(repo_object)


def create_product_from_installation_repositories(data):
    """
        Warning: not handling `repositories_removed` for now b/c
        there could be linked data which we don't want to destroy!
    """
    tenant, installation = find_tenant(data)

    # can't handle requests from unconfigured installation
    if not tenant:
        return

    with tenant_context(tenant):
        rpc = github_rpc_from_inst(installation)
        for repo in data.payload['repositories_added']:
            repo_object = rpc.get_repo(repo['full_name'])
            _product_from_repo(repo_object)
            _bugtracker_from_repo(repo_object)


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

    installation = AppInstallation.objects.create(
        installation=data.payload['installation']['id'],
        sender=data.sender,
        tenant_pk=tenant_pk,
        settings_url=data.payload['installation']['html_url'],
    )

    if tenant and tenant_pk:
        with tenant_context(tenant):
            rpc = github_rpc_from_inst(installation)
            for repository in data.payload['repositories']:
                repo_object = rpc.get_repo(repository['full_name'])
                _product_from_repo(repo_object)
                _bugtracker_from_repo(repo_object)


def create_version_from_tag(data):
    tenant, _installation = find_tenant(data)

    # can't handle requests from unconfigured installation
    if not tenant:
        return

    with tenant_context(tenant):
        # in case we've missed the repo creation hooks create a new Product & BugSystem
        create_product_from_repository(data)
        product = Product.objects.filter(name=data.payload['repository']['full_name']).first()

        if not product:
            return

        Version.objects.create(
            value=data.payload['ref'],
            product=product
        )


def resync_message(request, record, db_status):
    """
        Adds a response message indicating if a record was added or
        it already existed.
    """
    if db_status == RECORD_CREATED:
        messages.add_message(request,
                             messages.SUCCESS,
                             _("%s was imported from GitHub") % record)
    elif db_status == RECORD_EXISTS:
        messages.add_message(request,
                             messages.INFO,
                             _("%s already exists") % record)


def resync(request, app_inst):
    """
        Used when manually trigerring a resync. ATM only Product & BugSystem
        records are synced. Existing tags/Versions aren't added!
    """
    gh_inst = github_installation_from_inst(app_inst)

    for repo_object in gh_inst.get_repos():
        record, db_status = _product_from_repo(repo_object)
        resync_message(request, record, db_status)

        _bugtracker_from_repo(repo_object)
        resync_message(request, record, db_status)
