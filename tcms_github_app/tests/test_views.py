# Copyright (c) 2019-2020 Alexander Todorov <atodorov@MrSenko.com>

# Licensed under the GPL 3.0: https://www.gnu.org/licenses/gpl-3.0.txt
# pylint: disable=too-many-ancestors, too-many-lines

import json
from http import HTTPStatus
import unittest.mock

from django.urls import reverse
from django.conf import settings
from django.http import HttpResponseForbidden

from django_tenants.utils import get_tenant_model
from django_tenants.utils import get_tenant_domain_model
from django_tenants.utils import schema_context
from django_tenants.utils import tenant_context

from social_django.models import UserSocialAuth

from tcms.utils import github
from tcms.management.models import Classification
from tcms.management.models import Product
from tcms.management.models import Version
from tcms.testcases.models import BugSystem

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

    @unittest.mock.patch('tcms_github_app.utils.github_rpc_from_inst')
    def test_installation_configured_then_creates_new_product_and_bugsystem(self, github_rpc):
        test_repo = unittest.mock.MagicMock()
        test_repo.fork = False
        test_repo.full_name = 'kiwitcms-bot/test'
        test_repo.description = 'A test repository'
        test_repo.html_url = f'https://github.com/{test_repo.full_name}'

        github_rpc.return_value.get_repo = unittest.mock.MagicMock(side_effect=[test_repo])

        for schema_name in ['public', self.tenant.schema_name]:
            with schema_context(schema_name):
                self.assertFalse(Product.objects.filter(name='kiwitcms-bot/test').exists())
                self.assertFalse(
                    BugSystem.objects.filter(name='GitHub Issues for kiwitcms-bot/test').exists())

        # simulate already configured installation owned by the same user
        # who owns the GitHub repository
        app_inst = AppInstallationFactory(
            sender=self.social_user.uid,
            tenant_pk=self.tenant.pk,
        )

        # NOTE: testing with private repository b/c these are still added as products
        payload = """
{
  "action": "created",
  "repository": {
    "id": 225221463,
    "full_name": "kiwitcms-bot/test",
    "private": true,
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

            new_bugsystem = BugSystem.objects.get(name='GitHub Issues for kiwitcms-bot/test')
            self.assertEqual(new_bugsystem.tracker_type, 'tcms_github_app.issues.Integration')
            self.assertEqual(new_bugsystem.base_url, 'https://github.com/kiwitcms-bot/test')

    @unittest.mock.patch('tcms_github_app.utils.github_rpc_from_inst')
    def test_installation_configured_then_skip_forks(self, github_rpc):
        fork_repo = unittest.mock.MagicMock()
        fork_repo.fork = True

        github_rpc.return_value.get_repo = unittest.mock.MagicMock(side_effect=[fork_repo])

        for schema_name in ['public', self.tenant.schema_name]:
            with schema_context(schema_name):
                self.assertFalse(Product.objects.filter(name='kiwitcms-bot/fork').exists())
                self.assertFalse(
                    BugSystem.objects.filter(name='GitHub Issues for kiwitcms-bot/test').exists())

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
                self.assertFalse(
                    BugSystem.objects.filter(name='GitHub Issues for kiwitcms-bot/test').exists())

    def test_installation_unconfigured_then_nothing(self):
        for schema_name in ['public', self.tenant.schema_name]:
            with schema_context(schema_name):
                self.assertFalse(Product.objects.filter(name='kiwitcms-bot/test').exists())
                self.assertFalse(
                    BugSystem.objects.filter(name='GitHub Issues for kiwitcms-bot/test').exists())

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
                self.assertFalse(
                    BugSystem.objects.filter(name='GitHub Issues for kiwitcms-bot/test').exists())


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
                BugSystem.objects.all().delete()

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
    "html_url": "https://github.com/settings/installation/5651305",
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

    @unittest.mock.patch('tcms_github_app.utils.github_rpc_from_inst')
    def test_sender_only_has_access_to_public(self, github_rpc):
        example_repo = unittest.mock.MagicMock()
        example_repo.fork = False
        example_repo.full_name = 'kiwitcms-bot/example'
        example_repo.description = 'Example description'
        example_repo.html_url = f'https://github.com/{example_repo.full_name}'

        test_repo = unittest.mock.MagicMock()
        test_repo.fork = False
        test_repo.full_name = 'kiwitcms-bot/test'
        test_repo.description = 'Test description'
        test_repo.html_url = f'https://github.com/{test_repo.full_name}'

        github_rpc.return_value.get_repo = unittest.mock.MagicMock(
            side_effect=[example_repo, test_repo])

        # assert products don't exist initially
        for tenant in [self.public_tenant, self.tenant, self.private_tenant]:
            with tenant_context(tenant):
                self.assertFalse(Product.objects.filter(name='kiwitcms-bot/example').exists())
                self.assertFalse(Product.objects.filter(name='kiwitcms-bot/test').exists())
                self.assertFalse(
                    BugSystem.objects.filter(
                        name='GitHub Issues for kiwitcms-bot/example').exists())
                self.assertFalse(
                    BugSystem.objects.filter(
                        name='GitHub Issues for kiwitcms-bot/test').exists())

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
    "html_url": "https://github.com/settings/installations/5651305",
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
            self.assertTrue(
                BugSystem.objects.filter(
                    name='GitHub Issues for kiwitcms-bot/example').exists())
            self.assertTrue(
                BugSystem.objects.filter(
                    name='GitHub Issues for kiwitcms-bot/test').exists())

        # and not on other tenants
        for tenant in [self.tenant, self.private_tenant]:
            with tenant_context(tenant):
                self.assertFalse(Product.objects.filter(name='kiwitcms-bot/example').exists())
                self.assertFalse(Product.objects.filter(name='kiwitcms-bot/test').exists())
                self.assertFalse(
                    BugSystem.objects.filter(
                        name='GitHub Issues for kiwitcms-bot/example').exists())
                self.assertFalse(
                    BugSystem.objects.filter(
                        name='GitHub Issues for kiwitcms-bot/test').exists())

    @unittest.mock.patch('tcms_github_app.utils.github_rpc_from_inst')
    def test_sender_only_has_access_to_private_tenant(self, github_rpc):
        example_repo = unittest.mock.MagicMock()
        example_repo.fork = False
        example_repo.full_name = 'kiwitcms-bot/example'
        example_repo.description = 'Example description'
        example_repo.html_url = f'https://github.com/{example_repo.full_name}'

        test_repo = unittest.mock.MagicMock()
        test_repo.fork = False
        test_repo.full_name = 'kiwitcms-bot/test'
        test_repo.description = 'Test description'
        test_repo.html_url = f'https://github.com/{test_repo.full_name}'

        github_rpc.return_value.get_repo = unittest.mock.MagicMock(
            side_effect=[example_repo, test_repo])

        with schema_context('public'):
            # make sure social_user can access private_tenant
            self.private_tenant.authorized_users.add(self.social_user.user)

        # assert products don't exist initially
        for tenant in [self.public_tenant, self.tenant, self.private_tenant]:
            with tenant_context(tenant):
                self.assertFalse(Product.objects.filter(name='kiwitcms-bot/example').exists())
                self.assertFalse(Product.objects.filter(name='kiwitcms-bot/test').exists())
                self.assertFalse(
                    BugSystem.objects.filter(
                        name='GitHub Issues for kiwitcms-bot/example').exists())
                self.assertFalse(
                    BugSystem.objects.filter(
                        name='GitHub Issues for kiwitcms-bot/test').exists())

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
    "html_url": "https://github.com/settings/installations/5651305",
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
                self.assertFalse(
                    BugSystem.objects.filter(
                        name='GitHub Issues for kiwitcms-bot/example').exists())
                self.assertFalse(
                    BugSystem.objects.filter(
                        name='GitHub Issues for kiwitcms-bot/test').exists())

        with tenant_context(self.private_tenant):
            self.assertTrue(Product.objects.filter(name='kiwitcms-bot/example').exists())
            self.assertTrue(Product.objects.filter(name='kiwitcms-bot/test').exists())
            self.assertTrue(
                BugSystem.objects.filter(
                    name='GitHub Issues for kiwitcms-bot/example').exists())
            self.assertTrue(
                BugSystem.objects.filter(
                    name='GitHub Issues for kiwitcms-bot/test').exists())

    def test_sender_has_access_to_multiple_tenants(self):
        with schema_context('public'):
            self.private_tenant.authorized_users.add(self.social_user.user)
            self.tenant.authorized_users.add(self.social_user.user)

        # assert products don't exist initially
        for tenant in [self.public_tenant, self.tenant, self.private_tenant]:
            with tenant_context(tenant):
                self.assertFalse(Product.objects.filter(name='kiwitcms-bot/example').exists())
                self.assertFalse(Product.objects.filter(name='kiwitcms-bot/test').exists())
                self.assertFalse(
                    BugSystem.objects.filter(
                        name='GitHub Issues for kiwitcms-bot/example').exists())
                self.assertFalse(
                    BugSystem.objects.filter(
                        name='GitHub Issues for kiwitcms-bot/test').exists())

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
    "html_url": "https://github.com/settings/installations/5651399",
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
                self.assertFalse(
                    BugSystem.objects.filter(
                        name='GitHub Issues for kiwitcms-bot/example').exists())
                self.assertFalse(
                    BugSystem.objects.filter(
                        name='GitHub Issues for kiwitcms-bot/test').exists())


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


class HandleTagCreatedTestCase(AnonymousTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.url = reverse('github_app_webhook')
        cls.social_user = UserSocialAuthFactory()

    @unittest.mock.patch('tcms_github_app.utils.github_rpc_from_inst')
    def test_installation_configured_then_creates_new_version(self, github_rpc):
        example_repo = unittest.mock.MagicMock()
        example_repo.fork = False
        example_repo.full_name = 'kiwitcms-bot/example'
        example_repo.description = 'Example description'
        example_repo.html_url = f'https://github.com/{example_repo.full_name}'

        github_rpc.return_value.get_repo = unittest.mock.MagicMock(side_effect=[example_repo])

        for schema_name in ['public', self.tenant.schema_name]:
            with schema_context(schema_name):
                self.assertFalse(Version.objects.filter(value='v2.0').exists())

        # simulate already configured installation owned by the same user
        # who owns the GitHub repository
        app_inst = AppInstallationFactory(
            sender=self.social_user.uid,
            tenant_pk=self.tenant.pk,
        )

        payload = """
{
  "ref": "v2.0",
  "ref_type": "tag",
  "master_branch": "master",
  "description": "an empty repository",
  "pusher_type": "user",
  "repository": {
    "full_name": "kiwitcms-bot/example",
    "private": false,
    "owner": {
      "login": "kiwitcms-bot",
      "site_admin": false
    },
    "description": "an empty repository",
    "fork": false,
    "default_branch": "master"
  },
  "sender": {
    "login": "%s",
    "id": %d,
    "type": "User",
    "site_admin": false
  },
  "installation": {
    "id": %d,
    "node_id": "MDIzOkludGVncmF0aW9uSW5zdGFsbGF0aW9uNTY1MTMwNQ=="
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
                                    HTTP_X_GITHUB_EVENT='create')

        self.assertContains(response, 'ok')

        with tenant_context(self.tenant):
            self.assertTrue(Version.objects.filter(value='v2.0').exists())

    @unittest.mock.patch('tcms_github_app.utils.github_rpc_from_inst')
    def test_should_not_crash_when_version_already_exists(self, github_rpc):
        example_repo = unittest.mock.MagicMock()
        example_repo.fork = False
        example_repo.full_name = 'kiwitcms-bot/example'
        example_repo.description = 'Example description'
        example_repo.html_url = f'https://github.com/{example_repo.full_name}'

        github_rpc.return_value.get_repo = unittest.mock.MagicMock(side_effect=[example_repo])

        # make sure version already exists
        for schema_name in ['public', self.tenant.schema_name]:
            with schema_context(schema_name):
                classification, _ = Classification.objects.get_or_create(
                    name='test-products',
                )
                product, _ = Product.objects.get_or_create(
                    name=example_repo.full_name,
                    description=example_repo.description,
                    classification=classification,
                )
                Version.objects.get_or_create(product=product, value='v2.0')
                self.assertTrue(Version.objects.filter(value='v2.0').exists())

        # simulate already configured installation owned by the same user
        # who owns the GitHub repository
        app_inst = AppInstallationFactory(
            sender=self.social_user.uid,
            tenant_pk=self.tenant.pk,
        )

        payload = """
{
  "ref": "v2.0",
  "ref_type": "tag",
  "master_branch": "master",
  "description": "an empty repository",
  "pusher_type": "user",
  "repository": {
    "full_name": "kiwitcms-bot/example",
    "private": false,
    "owner": {
      "login": "kiwitcms-bot",
      "site_admin": false
    },
    "description": "an empty repository",
    "fork": false,
    "default_branch": "master"
  },
  "sender": {
    "login": "%s",
    "id": %d,
    "type": "User",
    "site_admin": false
  },
  "installation": {
    "id": %d,
    "node_id": "MDIzOkludGVncmF0aW9uSW5zdGFsbGF0aW9uNTY1MTMwNQ=="
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
                                    HTTP_X_GITHUB_EVENT='create')

        self.assertContains(response, 'ok')

        with tenant_context(self.tenant):
            self.assertTrue(Version.objects.filter(value='v2.0').exists())

    @unittest.mock.patch('tcms_github_app.utils.github_rpc_from_inst')
    def test_installation_configured_then_skip_forks(self, github_rpc):
        example_repo = unittest.mock.MagicMock()
        example_repo.fork = True

        github_rpc.return_value.get_repo = unittest.mock.MagicMock(side_effect=[example_repo])

        for schema_name in ['public', self.tenant.schema_name]:
            with schema_context(schema_name):
                self.assertFalse(Version.objects.filter(value='v2.0').exists())

        # simulate already configured installation owned by the same user
        # who owns the GitHub repository
        app_inst = AppInstallationFactory(
            sender=self.social_user.uid,
            tenant_pk=self.tenant.pk,
        )

        payload = """
{
  "ref": "v2.0",
  "ref_type": "tag",
  "master_branch": "master",
  "description": "an empty repository",
  "pusher_type": "user",
  "repository": {
    "full_name": "kiwitcms-bot/example",
    "private": false,
    "owner": {
      "login": "kiwitcms-bot",
      "site_admin": false
    },
    "description": "an empty repository",
    "fork": true,
    "default_branch": "master"
  },
  "sender": {
    "login": "%s",
    "id": %d,
    "type": "User",
    "site_admin": false
  },
  "installation": {
    "id": %d,
    "node_id": "MDIzOkludGVncmF0aW9uSW5zdGFsbGF0aW9uNTY1MTMwNQ=="
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
                                    HTTP_X_GITHUB_EVENT='create')

        self.assertContains(response, 'ok')

        # assert no versions for tags on fork repositories
        for schema_name in ['public', self.tenant.schema_name]:
            with schema_context(schema_name):
                self.assertFalse(Version.objects.filter(value='v2.0').exists())

    def test_installation_unconfigured_then_nothing(self):
        for schema_name in ['public', self.tenant.schema_name]:
            with schema_context(schema_name):
                self.assertFalse(Version.objects.filter(value='v2.0').exists())

        # simulate unconfigured installation owned by the same user
        # who owns the GitHub repository
        app_inst = AppInstallationFactory(
            sender=self.social_user.uid,
        )

        payload = """
{
  "ref": "v2.0",
  "ref_type": "tag",
  "master_branch": "master",
  "description": "an empty repository",
  "pusher_type": "user",
  "repository": {
    "full_name": "kiwitcms-bot/example",
    "private": false,
    "owner": {
      "login": "kiwitcms-bot",
      "site_admin": false
    },
    "description": "an empty repository",
    "fork": true,
    "default_branch": "master"
  },
  "sender": {
    "login": "%s",
    "id": %d,
    "type": "User",
    "site_admin": false
  },
  "installation": {
    "id": %d,
    "node_id": "MDIzOkludGVncmF0aW9uSW5zdGFsbGF0aW9uNTY1MTMwNQ=="
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
                                    HTTP_X_GITHUB_EVENT='create')

        self.assertContains(response, 'ok')

        # assert no new version have been created
        for schema_name in ['public', self.tenant.schema_name]:
            with schema_context(schema_name):
                self.assertFalse(Version.objects.filter(value='v2.0').exists())
