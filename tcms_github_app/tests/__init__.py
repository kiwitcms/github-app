# Copyright (c) 2019-2021 Alexander Todorov <atodorov@otb.bg>
#
# Licensed under GNU Affero General Public License v3 or later (AGPLv3+)
# https://www.gnu.org/licenses/agpl-3.0.html

# pylint: disable=too-many-ancestors

import factory
from factory.django import DjangoModelFactory

from tcms_tenants.tests import LoggedInTestCase
from tcms_tenants.tests import UserFactory


class AppInstallationFactory(DjangoModelFactory):
    class Meta:
        model = 'tcms_github_app.AppInstallation'

    installation = factory.Sequence(lambda n: n)
    sender = None
    tenant_pk = None


class UserSocialAuthFactory(DjangoModelFactory):
    class Meta:
        model = 'social_django.UserSocialAuth'

    user = factory.SubFactory(UserFactory)
    provider = 'github-app'
    uid = factory.Sequence(lambda n: n)


class AnonymousTestCase(LoggedInTestCase):
    def setUp(self):
        super().setUp()
        self.client.logout()
