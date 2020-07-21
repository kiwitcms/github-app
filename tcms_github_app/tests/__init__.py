# Copyright (c) 2019 Alexander Todorov <atodorov@MrSenko.com>

# Licensed under the GPL 3.0: https://www.gnu.org/licenses/gpl-3.0.txt

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


class ClassificationFactory(DjangoModelFactory):
    class Meta:
        model = 'management.Classification'
    name = factory.Sequence(lambda n: 'Classification %d' % n)


class ProductFactory(DjangoModelFactory):
    class Meta:
        model = 'management.Product'

    name = factory.Sequence(lambda n: 'Product %d' % n)
    classification = factory.SubFactory(ClassificationFactory)


class AnonymousTestCase(LoggedInTestCase):
    def setUp(self):
        super().setUp()
        self.client.logout()
