# Copyright (c) 2019 Alexander Todorov <atodorov@MrSenko.com>

# Licensed under the GPL 3.0: https://www.gnu.org/licenses/gpl-3.0.txt

from django import test
from django.conf import settings

import factory
from factory.django import DjangoModelFactory


class UserFactory(DjangoModelFactory):
    class Meta:
        model = settings.AUTH_USER_MODEL

    username = factory.Sequence(lambda n: 'User%d' % n)
    email = factory.LazyAttribute(
        lambda user: '%s@kiwitcms.org' % user.username)
    is_staff = True
    is_superuser = False


class LoggedInTestCase(test.TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.tester = UserFactory()
        cls.tester.set_password('password')
        cls.tester.save()

    def setUp(self):
        super().setUp()

        self.client.login(username=self.tester.username,
                          password='password')
