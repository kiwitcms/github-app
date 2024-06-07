# Copyright (c) 2019-2020 Alexander Todorov <atodorov@otb.bg>
#
# Licensed under GNU Affero General Public License v3 or later (AGPLv3+)
# https://www.gnu.org/licenses/agpl-3.0.html

# pylint: disable=too-many-ancestors

import json

from tcms_tenants.tests import UserFactory

from tcms_github_app import utils
from tcms_github_app.models import WebhookPayload
from tcms_github_app.tests import AnonymousTestCase
from tcms_github_app.tests import UserSocialAuthFactory


class FindTenantTestCase(AnonymousTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.social_user = UserSocialAuthFactory(
            user=UserFactory()
        )

    def test_for_missing_installation_returns_none(self):
        """
            find_tenant() shouldn't crash in case of race conditions where
            another webhook comes before we've saved the installation information
            in the DB!
        """

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
    "id": 99999999,
    "node_id": "MDIzOkludGVncmF0aW9uSW5zdGFsbGF0aW9uNTQ5ODkwOA=="
  }
}""".strip() % (self.social_user.user.username,
                self.social_user.uid)

        wh_payload = WebhookPayload.objects.create(
            event='repository',
            action='created',
            sender=self.social_user.uid,
            payload=json.loads(payload),
        )

        tenant, app_inst = utils.find_tenant(wh_payload)
        self.assertIsNone(tenant)
        self.assertIsNone(app_inst)
