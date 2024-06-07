# Copyright (c) 2019-2021 Alexander Todorov <atodorov@otb.bg>
#
# Licensed under GNU Affero General Public License v3 or later (AGPLv3+)
# https://www.gnu.org/licenses/agpl-3.0.html

# pylint: disable=too-many-ancestors

import unittest.mock

from django.urls import reverse
from django.http import HttpResponseForbidden

from django_tenants.utils import get_tenant_model
from django_tenants.utils import get_tenant_domain_model
from django_tenants.utils import schema_context

from tcms_tenants.tests import LoggedInTestCase

from tcms_github_app.models import WebhookPayload
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
                            f'<div class="grp-readonly">{app.installation}</div>',
                            html=True)
        self.assertContains(response,
                            f'<div class="grp-readonly">{app.sender}</div>',
                            html=True)

    def test_changelist_unauthorized_for_regular_user(self):
        with self.modify_settings(MIDDLEWARE={
                'remove': 'tcms_github_app.middleware.CheckGitHubAppMiddleware',
        }):
            response = self.client.get(
                reverse('admin:tcms_github_app_appinstallation_changelist'))
            self.assertIsInstance(response, HttpResponseForbidden)

    def test_changelist_authorized_for_superuser(self):
        self.tester.is_superuser = True
        self.tester.save()

        with self.modify_settings(MIDDLEWARE={
                'remove': 'tcms_github_app.middleware.CheckGitHubAppMiddleware',
        }):
            response = self.client.get(
                reverse('admin:tcms_github_app_appinstallation_changelist'))
            self.assertContains(response, 'App installations')

    def test_add_unauthorized_for_superuser(self):
        self.tester.is_superuser = True
        self.tester.save()

        with self.modify_settings(MIDDLEWARE={
                'remove': 'tcms_github_app.middleware.CheckGitHubAppMiddleware',
        }):
            response = self.client.get(reverse(
                'admin:tcms_github_app_appinstallation_add'))
            self.assertIsInstance(response, HttpResponseForbidden)

    def test_delete_unauthorized_for_superuser(self):
        self.tester.is_superuser = True
        self.tester.save()

        with self.modify_settings(MIDDLEWARE={
                'remove': 'tcms_github_app.middleware.CheckGitHubAppMiddleware',
        }):
            response = self.client.get(
                reverse('admin:tcms_github_app_appinstallation_delete', args=[self.app_inst.pk]))
            self.assertIsInstance(response, HttpResponseForbidden)

    def test_change_authorized_for_superuser(self):
        self.tester.is_superuser = True
        self.tester.save()

        with self.modify_settings(MIDDLEWARE={
                'remove': 'tcms_github_app.middleware.CheckGitHubAppMiddleware',
        }):
            response = self.client.get(
                reverse('admin:tcms_github_app_appinstallation_change', args=[self.app_inst.pk]))
            self.assert_fields(response, self.app_inst)
            self.assertNotContains(response, f'>[{self.get_test_schema_name()}] </option>')

    def test_change_authorized_for_owner(self):
        response = self.client.get(
            reverse('admin:tcms_github_app_appinstallation_change', args=[self.app_inst_tester.pk]))
        self.assert_fields(response, self.app_inst_tester)
        self.assertContains(response, f'>[{self.get_test_schema_name()}] </option>')

    def test_change_unauthorized_for_non_owner(self):
        with self.modify_settings(MIDDLEWARE={
                'remove': 'tcms_github_app.middleware.CheckGitHubAppMiddleware',
        }):
            response = self.client.get(
                reverse('admin:tcms_github_app_appinstallation_change', args=[self.app_inst.pk]))
            self.assertIsInstance(response, HttpResponseForbidden)

    @unittest.mock.patch('tcms_github_app.utils.resync')
    def test_save_by_owner_updates_installation(self, utils_resync):
        self.app_inst_tester.tenant_pk = None
        self.app_inst_tester.save()

        response = self.client.post(
            reverse('admin:tcms_github_app_appinstallation_change', args=[self.app_inst_tester.pk]),
            {
                'tenant_pk': self.tenant.pk,
            },
            follow=True,
        )

        self.assertRedirects(response, '/')
        self.assertContains(response, 'The app installation')
        self.assertContains(response, self.app_inst_tester)
        self.assertContains(response, 'was changed successfully.')

        self.app_inst_tester.refresh_from_db()
        self.assertEqual(self.app_inst_tester.tenant_pk, self.tenant.pk)

        # resync was triggered b/c we've updated tenant_pk
        utils_resync.assert_called_once()

    @unittest.mock.patch('tcms_github_app.utils.resync')
    def test_change_tenant_pk_to_empty_doesnt_resync(self, utils_resync):
        self.app_inst_tester.tenant_pk = self.tenant.pk
        self.app_inst_tester.save()

        # turning off middleware b/c it will redirect to the AppInst edit page
        with self.modify_settings(MIDDLEWARE={
                'remove': 'tcms_github_app.middleware.CheckGitHubAppMiddleware',
        }):
            response = self.client.post(
                reverse('admin:tcms_github_app_appinstallation_change',
                        args=[self.app_inst_tester.pk]),
                {
                    'tenant_pk': '',
                },
                follow=True,
            )

            self.assertRedirects(response, '/')
            self.assertContains(response, 'The app installation')
            self.assertContains(response, self.app_inst_tester)
            self.assertContains(response, 'was changed successfully.')

            self.app_inst_tester.refresh_from_db()
            self.assertIsNone(self.app_inst_tester.tenant_pk)

            # resync was not triggered b/c tenant_pk was set to None
            utils_resync.assert_not_called()

    @unittest.mock.patch('tcms_github_app.utils.resync')
    def test_save_not_changing_anything_doesnt_resync(self, utils_resync):
        self.app_inst_tester.tenant_pk = self.tenant.pk
        self.app_inst_tester.save()

        # this is the same as if user just pressed the Save button without making
        # any changes
        response = self.client.post(
            reverse('admin:tcms_github_app_appinstallation_change', args=[self.app_inst_tester.pk]),
            {
                'tenant_pk': self.tenant.pk,
            },
            follow=True,
        )

        self.assertRedirects(response, '/')
        self.assertContains(response, 'The app installation')
        self.assertContains(response, self.app_inst_tester)
        self.assertContains(response, 'was changed successfully.')

        self.app_inst_tester.refresh_from_db()
        self.assertEqual(self.app_inst_tester.tenant_pk, self.tenant.pk)

        # resync was not triggered b/c tenant_pk wasn't changed
        utils_resync.assert_not_called()


class WebhookPayloadAdminTestCase(LoggedInTestCase):
    def tearDown(self):
        self.tester.is_superuser = False
        self.tester.save()

    def test_changelist_unauthorized_for_regular_user(self):
        response = self.client.get(
            reverse('admin:tcms_github_app_webhookpayload_changelist'))
        self.assertIsInstance(response, HttpResponseForbidden)

    def test_changelist_authorized_for_superuser(self):
        self.tester.is_superuser = True
        self.tester.save()

        response = self.client.get(
            reverse('admin:tcms_github_app_webhookpayload_changelist'))
        self.assertContains(response, 'Webhook payloads')

    def test_add_unauthorized_for_superuser(self):
        self.tester.is_superuser = True
        self.tester.save()

        response = self.client.get(
            reverse('admin:tcms_github_app_webhookpayload_add'))
        self.assertIsInstance(response, HttpResponseForbidden)

    def test_delete_unauthorized_for_superuser(self):
        wh_payload = WebhookPayload.objects.create(
            event='repository',
            action='created',
            sender=999999,
            payload={'hello': 'world'},
        )

        self.tester.is_superuser = True
        self.tester.save()

        response = self.client.get(
            reverse('admin:tcms_github_app_webhookpayload_delete', args=[wh_payload.pk]))
        self.assertIsInstance(response, HttpResponseForbidden)

    def test_change_unauthorized_for_superuser(self):
        wh_payload = WebhookPayload.objects.create(
            event='repository',
            action='created',
            sender=999999,
            payload={'change': 'me'},
        )

        self.tester.is_superuser = True
        self.tester.save()

        response = self.client.get(
            reverse('admin:tcms_github_app_webhookpayload_change', args=[wh_payload.pk]))
        self.assertIsInstance(response, HttpResponseForbidden)
