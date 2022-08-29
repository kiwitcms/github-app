# Copyright (c) 2019-2021 Alexander Todorov <atodorov@MrSenko.com>

# Licensed under the GPL 3.0: https://www.gnu.org/licenses/gpl-3.0.txt
# pylint: disable=too-many-ancestors

from django.test import modify_settings
from django.urls import reverse

from tcms_tenants.tests import LoggedInTestCase

from tcms_github_app.tests import AppInstallationFactory
from tcms_github_app.tests import UserSocialAuthFactory


class CheckGitHubAppMiddlewareTestCase(LoggedInTestCase):
    @modify_settings(MIDDLEWARE={
        'append': 'tcms_github_app.middleware.CheckGitHubAppMiddleware',
    })
    def test_nothing_for_anonymous_user(self):
        self.client.logout()

        response = self.client.get('/', follow=True)

        self.assertContains(response, 'Welcome Guest')
        self.assertNotContains(response, 'Unconfigured GitHub App')

    @modify_settings(MIDDLEWARE={
        'append': 'tcms_github_app.middleware.CheckGitHubAppMiddleware',
    })
    def test_doesnt_redirect_for_regular_user_when_unconfigured_installation(self):
        # simulate unconfigured installation
        social_user = UserSocialAuthFactory(user=self.tester)
        app_inst = AppInstallationFactory(sender=int(social_user.uid))

        # self.tester != self.tenant.owner => will not redirect
        response = self.client.get('/', follow=True)
        self.assertNotContains(response, f'Unconfigured GitHub App {app_inst.installation}')

    @modify_settings(MIDDLEWARE={
        'append': 'tcms_github_app.middleware.CheckGitHubAppMiddleware',
    })
    def test_redirects_for_tenant_owner_when_unconfigured_installation(self):
        self.client.logout()
        self.client.login(
            username=self.tenant.owner.username,
            password='password',
        )

        # simulate unconfigured installation
        social_user = UserSocialAuthFactory(user=self.tenant.owner)
        app_inst = AppInstallationFactory(sender=int(social_user.uid))
        expected_url = reverse('admin:tcms_github_app_appinstallation_change',
                               args=[app_inst.pk])

        response = self.client.get('/', follow=True)

        self.assertRedirects(response, expected_url)
        self.assertContains(response, f'Unconfigured GitHub App {app_inst.installation}')

    @modify_settings(MIDDLEWARE={
        'append': 'tcms_github_app.middleware.CheckGitHubAppMiddleware',
    })
    def test_nothing_when_user_doesnt_have_social_auth(self):
        # simulate unconfigured installation but the current user
        # created his account via email/password, not GitHub so we
        # can't match the GitHub uid !
        AppInstallationFactory(sender=999999)

        response = self.client.get('/')

        self.assertContains(response, 'Kiwi TCMS - Dashboard')
        self.assertNotContains(response, 'Unconfigured GitHub App')

    @modify_settings(MIDDLEWARE={
        'append': 'tcms_github_app.middleware.CheckGitHubAppMiddleware',
    })
    def test_nothing_when_unconfigured_installation_not_owned_by_user(self):
        # simulate unconfigured installation by another user
        social_user = UserSocialAuthFactory()
        AppInstallationFactory(sender=int(social_user.uid))

        response = self.client.get('/')

        self.assertContains(response, 'Kiwi TCMS - Dashboard')
        self.assertNotContains(response, 'Unconfigured GitHub App')

    @modify_settings(MIDDLEWARE={
        'append': 'tcms_github_app.middleware.CheckGitHubAppMiddleware',
    })
    def test_dont_crash_with_keycloak(self):
        UserSocialAuthFactory(user=self.tester, uid="kc_atodorov")

        response = self.client.get('/', follow=True)

        self.assertContains(response, 'Dashboard')
