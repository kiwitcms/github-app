# Copyright (c) 2019 Alexander Todorov <atodorov@MrSenko.com>

# Licensed under the GPL 3.0: https://www.gnu.org/licenses/gpl-3.0.txt
# pylint: disable=too-many-ancestors

import json
from http import HTTPStatus

from django.urls import reverse
from django.conf import settings
from django.http import HttpResponseForbidden

from django_tenants.utils import tenant_context

from tcms.utils import github
from tcms.management.models import Product

from tcms_tenants.tests import UserFactory

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

    def test_creates_new_product(self):
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
