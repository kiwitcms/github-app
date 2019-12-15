# Copyright (c) 2019 Alexander Todorov <atodorov@MrSenko.com>

# Licensed under the GPL 3.0: https://www.gnu.org/licenses/gpl-3.0.txt
# pylint: disable=too-many-ancestors

from django.urls import reverse
from django.http import HttpResponseForbidden

from django_tenants.utils import get_tenant_model
from django_tenants.utils import get_tenant_domain_model
from django_tenants.utils import schema_context

from tcms_tenants.tests import LoggedInTestCase

from tcms_github_app.tests import AppInstallationFactory
from tcms_github_app.tests import UserSocialAuthFactory


class AppInstallationAdminTestCase(LoggedInTestCase):
    @classmethod
    def setUpClass(cls):
        get_tenant_model().auto_create_schema = True

        with schema_context('public'):
            # remove pre-existing tenants so they don't mess up the tests
            get_tenant_model().objects.exclude(schema_name='public').delete()

            # public tenant object b/c schema exists but not the Tenant itself!
            public_tenant = get_tenant_model().objects.filter(schema_name='public').first()
            if not public_tenant:
                public_tenant = get_tenant_model()(schema_name='public')
                cls.setup_tenant(public_tenant)
                public_tenant.save()

                public_domain = get_tenant_domain_model()(tenant=public_tenant,
                                                          domain='public.test.com')
                cls.setup_domain(public_domain)
                public_domain.save()

        super().setUpClass()

        social_user = UserSocialAuthFactory()
        cls.app_inst = AppInstallationFactory(sender=social_user.uid)

        social_tester = UserSocialAuthFactory(user=cls.tester)
        cls.app_inst_tester = AppInstallationFactory(sender=social_tester.uid)

    @classmethod
    def tearDownClass(cls):
        get_tenant_model().auto_create_schema = False
        super().tearDownClass()

    def tearDown(self):
        self.tester.is_superuser = False
        self.tester.save()

    def assert_fields(self, response, app):
        self.assertContains(response, 'Change app installation')
        self.assertContains(response, 'For additional configuration see')

        self.assertContains(response,
                            '>---------</option>')
        self.assertContains(response,
                            '>[public] </option>')
        self.assertContains(response,
                            '<div class="grp-readonly">%d</div>' % app.installation,
                            html=True)
        self.assertContains(response,
                            '<div class="grp-readonly">%d</div>' % app.sender,
                            html=True)

    def test_changelist_unauthorized_for_regular_user(self):
        response = self.client.get(
            reverse('admin:tcms_github_app_appinstallation_changelist'))
        self.assertIsInstance(response, HttpResponseForbidden)

    def test_changelist_authorized_for_superuser(self):
        self.tester.is_superuser = True
        self.tester.save()

        response = self.client.get(
            reverse('admin:tcms_github_app_appinstallation_changelist'))
        self.assertContains(response, 'App installations')

    def test_add_unauthorized_for_superuser(self):
        self.tester.is_superuser = True
        self.tester.save()

        response = self.client.get(
            reverse('admin:tcms_github_app_appinstallation_add'))
        self.assertIsInstance(response, HttpResponseForbidden)

    def test_delete_unauthorized_for_superuser(self):
        self.tester.is_superuser = True
        self.tester.save()

        response = self.client.get(
            reverse('admin:tcms_github_app_appinstallation_delete', args=[self.app_inst.pk]))
        self.assertIsInstance(response, HttpResponseForbidden)

    def test_change_authorized_for_superuser(self):
        self.tester.is_superuser = True
        self.tester.save()

        response = self.client.get(
            reverse('admin:tcms_github_app_appinstallation_change', args=[self.app_inst.pk]))
        self.assert_fields(response, self.app_inst)

    def test_change_authorized_for_owner(self):
        response = self.client.get(
            reverse('admin:tcms_github_app_appinstallation_change', args=[self.app_inst_tester.pk]))
        self.assert_fields(response, self.app_inst_tester)

    def test_change_unauthorized_for_non_owner(self):
        response = self.client.get(
            reverse('admin:tcms_github_app_appinstallation_change', args=[self.app_inst.pk]))
        self.assertIsInstance(response, HttpResponseForbidden)
