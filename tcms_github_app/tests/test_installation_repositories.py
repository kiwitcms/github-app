# Copyright (c) 2020-2021 Alexander Todorov <atodorov@MrSenko.com>

# Licensed under the GPL 3.0: https://www.gnu.org/licenses/gpl-3.0.txt
# pylint: disable=too-many-ancestors

import json
import unittest.mock

from django.urls import reverse
from django.conf import settings

from django_tenants.utils import schema_context
from django_tenants.utils import tenant_context

from tcms.utils import github
from tcms.management.models import Product
from tcms.testcases.models import BugSystem
from tcms.tests.factories import ProductFactory

from tcms_github_app.tests import AnonymousTestCase
from tcms_github_app.tests import AppInstallationFactory
from tcms_github_app.tests import UserSocialAuthFactory


class HandleInstallationRepositoriesTestCase(AnonymousTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.url = reverse('github_app_webhook')
        cls.social_user = UserSocialAuthFactory()

    @unittest.mock.patch('tcms_github_app.utils.github_rpc_from_inst')
    def test_adds_new_data_when_it_doesnt_exist(self, github_rpc):
        mock_repo = unittest.mock.MagicMock()
        mock_repo.fork = False
        mock_repo.full_name = 'kiwitcms-bot/IT-CPE'
        mock_repo.description = ''
        mock_repo.html_url = 'https://github.com/%s' % mock_repo.full_name

        github_rpc.return_value.get_repo = unittest.mock.MagicMock(side_effect=[mock_repo])

        # assert products don't exist initially
        for schema_name in ['public', self.tenant.schema_name]:
            with schema_context(schema_name):
                self.assertFalse(Product.objects.filter(name='kiwitcms-bot/IT-CPE').exists())
                self.assertFalse(
                    BugSystem.objects.filter(
                        name='GitHub Issues for kiwitcms-bot/IT-CPE').exists())

        # simulate already configured installation owned by the same user
        # who owns the GitHub repository
        app_inst = AppInstallationFactory(
            sender=self.social_user.uid,
            tenant_pk=self.tenant.pk,
        )

        payload = """
{
  "action": "added",
  "installation": {
    "id": %d,
    "account": {
    },
    "repository_selection": "all",
    "single_file_name": null
  },
  "repository_selection": "all",
  "repositories_added": [
    {
      "id": 281502467,
      "node_id": "MDEwOlJlcG9zaXRvcnkyODE1MDI0Njc=",
      "name": "IT-CPE",
      "full_name": "kiwitcms-bot/IT-CPE",
      "private": false
    }
  ],
  "repositories_removed": [

  ],
  "requester": null,
  "sender": {
    "login": "%s",
    "id": %d
  }
}""".strip() % (app_inst.installation,
                self.social_user.user.username,
                self.social_user.uid)

        signature = github.calculate_signature(
            settings.KIWI_GITHUB_APP_SECRET,
            json.dumps(json.loads(payload)).encode())

        response = self.client.post(self.url,
                                    json.loads(payload),
                                    content_type='application/json',
                                    HTTP_X_HUB_SIGNATURE=signature,
                                    HTTP_X_GITHUB_EVENT='installation_repositories')

        self.assertContains(response, 'ok')

        # assert products have been imported *ONLY* on public
        with tenant_context(self.tenant):
            new_product = Product.objects.get(name='kiwitcms-bot/IT-CPE')
            self.assertEqual(new_product.description, 'GitHub repository')

            new_bugsystem = BugSystem.objects.get(name='GitHub Issues for kiwitcms-bot/IT-CPE')
            self.assertEqual(new_bugsystem.tracker_type, 'tcms_github_app.issues.Integration')
            self.assertEqual(new_bugsystem.base_url, 'https://github.com/kiwitcms-bot/IT-CPE')

    @unittest.mock.patch('tcms_github_app.utils.github_rpc_from_inst')
    def test_doesnt_crash_when_data_exists(self, github_rpc):
        mock_repo = unittest.mock.MagicMock()
        mock_repo.fork = False
        mock_repo.full_name = 'kiwitcms-bot/IT'
        mock_repo.description = ''
        mock_repo.html_url = 'https://github.com/%s' % mock_repo.full_name

        github_rpc.return_value.get_repo = unittest.mock.MagicMock(side_effect=[mock_repo])

        # make sure Product & BugSystem exist first
        with tenant_context(self.tenant):
            if not Product.objects.filter(name='kiwitcms-bot/IT').exists():
                ProductFactory(name='kiwitcms-bot/IT')
            self.assertTrue(Product.objects.filter(name='kiwitcms-bot/IT').exists())

            if not BugSystem.objects.filter(
                    name='GitHub Issues for kiwitcms-bot/IT').exists():
                BugSystem.objects.get_or_create(
                    name='GitHub Issues for kiwitcms-bot/IT',
                    tracker_type='tcms_github_app.issues.Integration',
                    base_url='https://github.com/kiwitcms-bot/IT',
                )
            self.assertTrue(BugSystem.objects.filter(
                name='GitHub Issues for kiwitcms-bot/IT').exists())

        # simulate already configured installation owned by the same user
        # who owns the GitHub repository
        app_inst = AppInstallationFactory(
            sender=self.social_user.uid,
            tenant_pk=self.tenant.pk,
        )

        payload = """
{
  "action": "added",
  "installation": {
    "id": %d,
    "account": {
    },
    "repository_selection": "all",
    "single_file_name": null
  },
  "repository_selection": "all",
  "repositories_added": [
    {
      "id": 281502467,
      "node_id": "MDEwOlJlcG9zaXRvcnkyODE1MDI0Njc=",
      "name": "IT",
      "full_name": "kiwitcms-bot/IT",
      "private": false
    }
  ],
  "repositories_removed": [

  ],
  "requester": null,
  "sender": {
    "login": "%s",
    "id": %d
  }
}""".strip() % (app_inst.installation,
                self.social_user.user.username,
                self.social_user.uid)

        signature = github.calculate_signature(
            settings.KIWI_GITHUB_APP_SECRET,
            json.dumps(json.loads(payload)).encode())

        response = self.client.post(self.url,
                                    json.loads(payload),
                                    content_type='application/json',
                                    HTTP_X_HUB_SIGNATURE=signature,
                                    HTTP_X_GITHUB_EVENT='installation_repositories')

        self.assertContains(response, 'ok')

        # assert products have been imported *ONLY* on public
        with tenant_context(self.tenant):
            new_product = Product.objects.get(name='kiwitcms-bot/IT')
            self.assertEqual(new_product.description, '')

            new_bugsystem = BugSystem.objects.get(name='GitHub Issues for kiwitcms-bot/IT')
            self.assertEqual(new_bugsystem.tracker_type, 'tcms_github_app.issues.Integration')
            self.assertEqual(new_bugsystem.base_url, 'https://github.com/kiwitcms-bot/IT')
