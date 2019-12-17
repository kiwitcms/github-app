# Copyright (c) 2019 Alexander Todorov <atodorov@MrSenko.com>

# Licensed under the GPL 3.0: https://www.gnu.org/licenses/gpl-3.0.txt
# pylint: disable=too-many-ancestors

import json
from http import HTTPStatus

from django.urls import reverse
from django.conf import settings
from django.http import HttpResponseForbidden

from django_tenants.utils import get_tenant_model
from django_tenants.utils import get_tenant_domain_model
from django_tenants.utils import schema_context
from django_tenants.utils import tenant_context

from social_django.models import UserSocialAuth

from tcms.utils import github
from tcms.management.models import Product

from tcms_tenants.tests import LoggedInTestCase
from tcms_tenants.tests import UserFactory

from tcms_github_app.models import AppInstallation
from tcms_github_app.models import WebhookPayload
from tcms_github_app.tests import AnonymousTestCase
from tcms_github_app.tests import AppInstallationFactory
from tcms_github_app.tests import UserSocialAuthFactory


class WebHookTestCase(AnonymousTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.url = reverse('github_app_webhook')

    def test_hook_ping(self):
        payload = """
{
  "zen": "Mind your words, they are important.",
  "sender": {
    "login": "atodorov",
    "id": 1002300
  }
}
""".strip()
        signature = github.calculate_signature(
            settings.KIWI_GITHUB_APP_SECRET,
            json.dumps(json.loads(payload)).encode())
        response = self.client.post(self.url,
                                    json.loads(payload),
                                    content_type='application/json',
                                    HTTP_X_HUB_SIGNATURE=signature,
                                    HTTP_X_GITHUB_EVENT='ping')

        # initial ping responds with a pong
        self.assertContains(response, 'pong')

    def test_without_signature_header(self):
        payload = json.loads("""
{
  "zen": "Mind your words, they are important.",
  "sender": {
    "login": "atodorov",
    "id": 1002300
  }
}
""".strip())

        response = self.client.post(
            self.url, payload, content_type='application/json')

        # missing signature should cause failure
        self.assertIsInstance(response, HttpResponseForbidden)
        self.assertEqual(HTTPStatus.FORBIDDEN, response.status_code)

    def test_with_valid_signature_header(self):
        payload = """
{
  "action": "will-be-saved-in-db",
  "sender": {
    "login": "kiwitcms-bot",
    "id": 1002300
  }
}
""".strip()

        signature = github.calculate_signature(
            settings.KIWI_GITHUB_APP_SECRET,
            json.dumps(json.loads(payload)).encode())

        initial_db_count = WebhookPayload.objects.count()

        response = self.client.post(self.url,
                                    json.loads(payload),
                                    content_type='application/json',
                                    HTTP_X_HUB_SIGNATURE=signature,
                                    HTTP_X_GITHUB_EVENT='some-event')
        self.assertContains(response, 'ok')

        # the hook handler saves to DB
        self.assertEqual(initial_db_count + 1, WebhookPayload.objects.count())

    def test_with_valid_signature_header_without_event_header(self):
        payload = """
{
  "action": "will-be-saved-in-db",
  "sender": {
    "login": "kiwitcms-bot",
    "id": 1002300
  }
}
""".strip()

        signature = github.calculate_signature(
            settings.KIWI_GITHUB_APP_SECRET,
            json.dumps(json.loads(payload)).encode())

        # X-GitHub-Event header is missing !!!
        response = self.client.post(self.url,
                                    json.loads(payload),
                                    content_type='application/json',
                                    HTTP_X_HUB_SIGNATURE=signature)

        self.assertIsInstance(response, HttpResponseForbidden)
        self.assertContains(response,
                            'Missing event',
                            status_code=HTTPStatus.FORBIDDEN)


class HandleRepositoryCreatedTestCase(AnonymousTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.url = reverse('github_app_webhook')
        cls.social_user = UserSocialAuthFactory(
            user=UserFactory(username='kiwitcms-bot')
        )

    def test_installation_configured_then_creates_new_product(self):
        for schema_name in ['public', self.tenant.schema_name]:
            with schema_context(schema_name):
                self.assertFalse(Product.objects.filter(name='kiwitcms-bot/test').exists())

        # simulate already configured installation owned by the same user
        # who owns the GitHub repository
        app_inst = AppInstallationFactory(
            sender=self.social_user.uid,
            tenant_pk=self.tenant.pk,
        )

        payload = """
{
  "action": "created",
  "repository": {
    "id": 225221463,
    "full_name": "kiwitcms-bot/test",
    "private": false,
    "owner": {
    },
    "html_url": "https://github.com/kiwitcms-bot/test",
    "description": "A test repository",
    "fork": false
  },
  "sender": {
    "login": "%s",
    "id": %d
  },
  "installation": {
    "id": %d,
    "node_id": "MDIzOkludGVncmF0aW9uSW5zdGFsbGF0aW9uNTQ5ODkwOA=="
  }
}""".strip() % (self.social_user.user.username,
                self.social_user.uid,
                app_inst.installation)

        signature = github.calculate_signature(
            settings.KIWI_GITHUB_APP_SECRET,
            json.dumps(json.loads(payload)).encode())

        response = self.client.post(self.url,
                                    json.loads(payload),
                                    content_type='application/json',
                                    HTTP_X_HUB_SIGNATURE=signature,
                                    HTTP_X_GITHUB_EVENT='repository')

        self.assertContains(response, 'ok')

        with tenant_context(self.tenant):
            new_product = Product.objects.get(name='kiwitcms-bot/test')
            self.assertEqual(new_product.description, 'A test repository')

    def test_installation_configured_then_skip_forks(self):
        for schema_name in ['public', self.tenant.schema_name]:
            with schema_context(schema_name):
                self.assertFalse(Product.objects.filter(name='kiwitcms-bot/fork').exists())

        # simulate already configured installation owned by the same user
        # who owns the GitHub repository
        app_inst = AppInstallationFactory(
            sender=self.social_user.uid,
            tenant_pk=self.tenant.pk,
        )

        payload = """
{
  "action": "created",
  "repository": {
    "id": 225221463,
    "full_name": "kiwitcms-bot/fork",
    "private": false,
    "owner": {
    },
    "html_url": "https://github.com/kiwitcms-bot/fork",
    "description": "A fork repository",
    "fork": true
  },
  "sender": {
    "login": "%s",
    "id": %d
  },
  "installation": {
    "id": %d,
    "node_id": "MDIzOkludGVncmF0aW9uSW5zdGFsbGF0aW9uNTQ5ODkwOA=="
  }
}""".strip() % (self.social_user.user.username,
                self.social_user.uid,
                app_inst.installation)

        signature = github.calculate_signature(
            settings.KIWI_GITHUB_APP_SECRET,
            json.dumps(json.loads(payload)).encode())

        response = self.client.post(self.url,
                                    json.loads(payload),
                                    content_type='application/json',
                                    HTTP_X_HUB_SIGNATURE=signature,
                                    HTTP_X_GITHUB_EVENT='repository')

        self.assertContains(response, 'ok')

        # assert no products for forks
        for schema_name in ['public', self.tenant.schema_name]:
            with schema_context(schema_name):
                self.assertFalse(Product.objects.filter(name='kiwitcms-bot/fork').exists())

    def test_installation_unconfigured_then_nothing(self):
        for schema_name in ['public', self.tenant.schema_name]:
            with schema_context(schema_name):
                self.assertFalse(Product.objects.filter(name='kiwitcms-bot/test').exists())

        # simulate unconfigured installation owned by the same user
        # who owns the GitHub repository
        app_inst = AppInstallationFactory(
            sender=self.social_user.uid,
        )

        payload = """
{
  "action": "created",
  "repository": {
    "id": 225221463,
    "full_name": "kiwitcms-bot/test",
    "private": false,
    "owner": {
    },
    "html_url": "https://github.com/kiwitcms-bot/test",
    "description": "A test repository",
    "fork": false
  },
  "sender": {
    "login": "%s",
    "id": %d
  },
  "installation": {
    "id": %d,
    "node_id": "MDIzOkludGVncmF0aW9uSW5zdGFsbGF0aW9uNTQ5ODkwOA=="
  }
}""".strip() % (self.social_user.user.username,
                self.social_user.uid,
                app_inst.installation)

        signature = github.calculate_signature(
            settings.KIWI_GITHUB_APP_SECRET,
            json.dumps(json.loads(payload)).encode())

        response = self.client.post(self.url,
                                    json.loads(payload),
                                    content_type='application/json',
                                    HTTP_X_HUB_SIGNATURE=signature,
                                    HTTP_X_GITHUB_EVENT='repository')

        self.assertContains(response, 'ok')

        # assert no new products have been created
        for schema_name in ['public', self.tenant.schema_name]:
            with schema_context(schema_name):
                self.assertFalse(Product.objects.filter(name='kiwitcms-bot/test').exists())


class HandleInstallationCreatedTestCase(AnonymousTestCase):
    @classmethod
    def setUpClass(cls):
        # we really need private schema to be created on disk
        # otherwise tenant_context() operations still create
        # objects into public schema!
        get_tenant_model().auto_create_schema = True

        cls.url = reverse('github_app_webhook')

        with schema_context('public'):
            # remove pre-existing tenants so they don't mess up the tests
            get_tenant_model().objects.exclude(schema_name='public').delete()

            cls.social_user = UserSocialAuthFactory(
                user=UserFactory()
            )

            # public tenant object b/c schema exists but not the Tenant itself!
            cls.public_tenant = get_tenant_model().objects.filter(schema_name='public').first()
            if not cls.public_tenant:
                cls.public_tenant = get_tenant_model()(schema_name='public')
                cls.setup_tenant(cls.public_tenant)
                cls.public_tenant.save()

                public_domain = get_tenant_domain_model()(tenant=cls.public_tenant,
                                                          domain='public.test.com')
                cls.setup_domain(public_domain)
                public_domain.save()

            # private tenant for some tests
            cls.private_tenant = get_tenant_model()(schema_name='private')
            cls.setup_tenant(cls.private_tenant)
            cls.private_tenant.save()

            cls.private_domain = get_tenant_domain_model()(tenant=cls.private_tenant,
                                                           domain='private.test.com')
            cls.setup_domain(cls.private_domain)
            cls.private_domain.save()

        # create self.tenant after public & private
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        # because some tests really need the schema present on disk
        # while by default we don't create it to save execuion time
        get_tenant_model().auto_create_schema = False

    def tearDown(self):
        with schema_context('public'):
            # reset tenant access after each test
            self.private_tenant.authorized_users.clear()
            self.tenant.authorized_users.clear()

        # delete products b/c we use the same payload for multiple tests
        # and sometimes there can be duplicates from a previous test
        for tenant in [self.public_tenant, self.private_tenant, self.tenant]:
            with tenant_context(tenant):
                Product.objects.all().delete()

    def test_sender_not_in_db(self):
        with schema_context('public'):
            initial_installation_count = AppInstallation.objects.count()

        payload = """
{
  "action": "created",
  "installation": {
    "id": 5651305,
    "account": {
      "login": "kiwitcms-bot",
      "id": 44892260,
      "site_admin": false
    },
    "repository_selection": "all",
    "single_file_name": null
  },
  "repositories": [
    {
      "id": 224524413,
      "node_id": "MDEwOlJlcG9zaXRvcnkyMjQ1MjQ0MTM=",
      "name": "example",
      "full_name": "kiwitcms-bot/example",
      "private": false
    },
    {
      "id": 225221463,
      "node_id": "MDEwOlJlcG9zaXRvcnkyMjUyMjE0NjM=",
      "name": "test",
      "full_name": "kiwitcms-bot/test",
      "private": false
    }
  ],
  "requester": null,
  "sender": {
    "login": "kiwitcms-bot",
    "id": 99999999,
    "site_admin": false
  }
}""".strip()

        signature = github.calculate_signature(
            settings.KIWI_GITHUB_APP_SECRET,
            json.dumps(json.loads(payload)).encode())

        response = self.client.post(self.url,
                                    json.loads(payload),
                                    content_type='application/json',
                                    HTTP_X_HUB_SIGNATURE=signature,
                                    HTTP_X_GITHUB_EVENT='installation')

        self.assertContains(response, 'ok')

        with schema_context('public'):
            self.assertEqual(
                initial_installation_count + 1,
                AppInstallation.objects.count())
            self.assertTrue(
                AppInstallation.objects.filter(installation=5651305,
                                               sender=99999999,
                                               tenant_pk=None).exists())

    def test_sender_only_has_access_to_public(self):
        # assert products don't exist initially
        for tenant in [self.public_tenant, self.tenant, self.private_tenant]:
            with tenant_context(tenant):
                self.assertFalse(Product.objects.filter(name='kiwitcms-bot/example').exists())
                self.assertFalse(Product.objects.filter(name='kiwitcms-bot/test').exists())

        payload = """
{
  "action": "created",
  "installation": {
    "id": 5651305,
    "account": {
      "login": "kiwitcms-bot",
      "id": 44892260,
      "site_admin": false
    },
    "repository_selection": "all",
    "single_file_name": null
  },
  "repositories": [
    {
      "id": 224524413,
      "node_id": "MDEwOlJlcG9zaXRvcnkyMjQ1MjQ0MTM=",
      "name": "example",
      "full_name": "kiwitcms-bot/example",
      "private": false
    },
    {
      "id": 225221463,
      "node_id": "MDEwOlJlcG9zaXRvcnkyMjUyMjE0NjM=",
      "name": "test",
      "full_name": "kiwitcms-bot/test",
      "private": false
    }
  ],
  "requester": null,
  "sender": {
    "login": "%s",
    "id": %d,
    "site_admin": false
  }
}""".strip() % (self.social_user.user.username, self.social_user.uid)

        signature = github.calculate_signature(
            settings.KIWI_GITHUB_APP_SECRET,
            json.dumps(json.loads(payload)).encode())

        response = self.client.post(self.url,
                                    json.loads(payload),
                                    content_type='application/json',
                                    HTTP_X_HUB_SIGNATURE=signature,
                                    HTTP_X_GITHUB_EVENT='installation')

        self.assertContains(response, 'ok')

        with schema_context('public'):
            self.assertTrue(
                AppInstallation.objects.filter(installation=5651305,
                                               sender=self.social_user.uid,
                                               tenant_pk=self.public_tenant.pk).exists())

        # assert products have been imported *ONLY* on public
        with schema_context('public'):
            self.assertTrue(Product.objects.filter(name='kiwitcms-bot/example').exists())
            self.assertTrue(Product.objects.filter(name='kiwitcms-bot/test').exists())

        # and not on other tenants
        for tenant in [self.tenant, self.private_tenant]:
            with tenant_context(tenant):
                self.assertFalse(Product.objects.filter(name='kiwitcms-bot/example').exists())
                self.assertFalse(Product.objects.filter(name='kiwitcms-bot/test').exists())

    def test_sender_only_has_access_to_private_tenant(self):
        with schema_context('public'):
            # make sure social_user can access private_tenant
            self.private_tenant.authorized_users.add(self.social_user.user)

        # assert products don't exist initially
        for tenant in [self.public_tenant, self.tenant, self.private_tenant]:
            with tenant_context(tenant):
                self.assertFalse(Product.objects.filter(name='kiwitcms-bot/example').exists())
                self.assertFalse(Product.objects.filter(name='kiwitcms-bot/test').exists())

        payload = """
{
  "action": "created",
  "installation": {
    "id": 5651305,
    "account": {
      "login": "kiwitcms-bot",
      "id": 44892260,
      "site_admin": false
    },
    "repository_selection": "all",
    "single_file_name": null
  },
  "repositories": [
    {
      "id": 224524413,
      "node_id": "MDEwOlJlcG9zaXRvcnkyMjQ1MjQ0MTM=",
      "name": "example",
      "full_name": "kiwitcms-bot/example",
      "private": false
    },
    {
      "id": 225221463,
      "node_id": "MDEwOlJlcG9zaXRvcnkyMjUyMjE0NjM=",
      "name": "test",
      "full_name": "kiwitcms-bot/test",
      "private": false
    }
  ],
  "requester": null,
  "sender": {
    "login": "%s",
    "id": %d,
    "site_admin": false
  }
}""".strip() % (self.social_user.user.username, self.social_user.uid)

        signature = github.calculate_signature(
            settings.KIWI_GITHUB_APP_SECRET,
            json.dumps(json.loads(payload)).encode())

        response = self.client.post(self.url,
                                    json.loads(payload),
                                    content_type='application/json',
                                    HTTP_X_HUB_SIGNATURE=signature,
                                    HTTP_X_GITHUB_EVENT='installation')

        self.assertContains(response, 'ok')

        with schema_context('public'):
            self.assertTrue(
                AppInstallation.objects.filter(installation=5651305,
                                               sender=self.social_user.uid,
                                               tenant_pk=self.private_tenant.pk).exists())

        # assert products have been imported *ONLY* on private.tenant
        for tenant in [self.public_tenant, self.tenant]:
            with tenant_context(tenant):
                self.assertFalse(Product.objects.filter(name='kiwitcms-bot/example').exists())
                self.assertFalse(Product.objects.filter(name='kiwitcms-bot/test').exists())

        with tenant_context(self.private_tenant):
            self.assertTrue(Product.objects.filter(name='kiwitcms-bot/example').exists())
            self.assertTrue(Product.objects.filter(name='kiwitcms-bot/test').exists())

    def test_sender_has_access_to_multiple_tenants(self):
        with schema_context('public'):
            self.private_tenant.authorized_users.add(self.social_user.user)
            self.tenant.authorized_users.add(self.social_user.user)

        # assert products don't exist initially
        for tenant in [self.public_tenant, self.tenant, self.private_tenant]:
            with tenant_context(tenant):
                self.assertFalse(Product.objects.filter(name='kiwitcms-bot/example').exists())
                self.assertFalse(Product.objects.filter(name='kiwitcms-bot/test').exists())

        payload = """
{
  "action": "created",
  "installation": {
    "id": 5651399,
    "account": {
      "login": "kiwitcms-bot",
      "id": 44892260,
      "site_admin": false
    },
    "repository_selection": "all",
    "single_file_name": null
  },
  "repositories": [
    {
      "id": 224524413,
      "node_id": "MDEwOlJlcG9zaXRvcnkyMjQ1MjQ0MTM=",
      "name": "example",
      "full_name": "kiwitcms-bot/example",
      "private": false
    },
    {
      "id": 225221463,
      "node_id": "MDEwOlJlcG9zaXRvcnkyMjUyMjE0NjM=",
      "name": "test",
      "full_name": "kiwitcms-bot/test",
      "private": false
    }
  ],
  "requester": null,
  "sender": {
    "login": "%s",
    "id": %d,
    "site_admin": false
  }
}""".strip() % (self.social_user.user.username, self.social_user.uid)

        signature = github.calculate_signature(
            settings.KIWI_GITHUB_APP_SECRET,
            json.dumps(json.loads(payload)).encode())

        response = self.client.post(self.url,
                                    json.loads(payload),
                                    content_type='application/json',
                                    HTTP_X_HUB_SIGNATURE=signature,
                                    HTTP_X_GITHUB_EVENT='installation')

        self.assertContains(response, 'ok')

        with schema_context('public'):
            self.assertTrue(
                AppInstallation.objects.filter(installation=5651399,
                                               sender=self.social_user.uid,
                                               tenant_pk=None).exists())

        # assert products have *NOT* been imported anywhere
        for tenant in [self.public_tenant, self.tenant, self.private_tenant]:
            with tenant_context(tenant):
                self.assertFalse(Product.objects.filter(name='kiwitcms-bot/example').exists())
                self.assertFalse(Product.objects.filter(name='kiwitcms-bot/test').exists())


class ApplicationEditTestCase(LoggedInTestCase):
    def tearDown(self):
        UserSocialAuth.objects.filter(user=self.tester).delete()
        AppInstallation.objects.all().delete()

    def test_warns_user_without_social_auth(self):
        response = self.client.get(reverse('github_app_edit'), follow=True)

        self.assertRedirects(response, '/')
        self.assertContains(response, 'You have not logged-in via GitHub account')

    def test_warns_user_without_application(self):
        UserSocialAuthFactory(user=self.tester)

        response = self.client.get(reverse('github_app_edit'), follow=True)

        self.assertRedirects(response, '/')
        self.assertContains(response, 'You have not installed Kiwi TCMS into your GitHub account')

    def test_redirects_if_single_application(self):
        social_user = UserSocialAuthFactory(user=self.tester)
        app_inst = AppInstallationFactory(sender=social_user.uid, tenant_pk=self.tenant.pk)

        response = self.client.get(reverse('github_app_edit'), follow=True)

        self.assertRedirects(
            response,
            reverse('admin:tcms_github_app_appinstallation_change',
                    args=[app_inst.pk]))
        self.assertContains(response, 'Change app installation')
        self.assertContains(response, 'For additional configuration see')

    def test_warns_user_with_multiple_applications(self):
        social_user = UserSocialAuthFactory(user=self.tester)

        app_one = AppInstallationFactory(sender=social_user.uid, tenant_pk=self.tenant.pk)
        app_two = AppInstallationFactory(sender=social_user.uid, tenant_pk=self.tenant.pk)
        app_three = AppInstallationFactory(sender=social_user.uid, tenant_pk=self.tenant.pk)

        response = self.client.get(reverse('github_app_edit'), follow=True)

        self.assertRedirects(response, '/')
        self.assertContains(response, 'Multiple GitHub App installations detected! See below:')
        for app in [app_one, app_two, app_three]:
            expected_url = reverse('admin:tcms_github_app_appinstallation_change',
                                   args=[app.pk])
            self.assertContains(response, expected_url)
