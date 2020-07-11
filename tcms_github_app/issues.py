# Copyright (c) 2020 Alexander Todorov <atodorov@MrSenko.com>
#
# Licensed under the GPL 3.0: https://www.gnu.org/licenses/gpl-3.0.txt
#

import github
from django.conf import settings
from django.core.cache import cache

from tcms.issuetracker.types import GitHub
from tcms_github_app.models import AppInstallation


class Integration(GitHub):
    """
        A Kiwi TCMS external bug tracker integration for GitHub which
        authenticates as an installed GitHub App instead of with a personal
        token!

        Requires:

        :base_url: - URL to a GitHub repository for which we're going to report issues

        .. note::

            The ``api_password`` field is determined at runtime!
    """
    @staticmethod
    def _find_token(gh_app, installation):
        """
            Find an installation access token for this app:
            https://docs.github.com/en/rest/reference/apps#create-an-installation-access-token-for-an-app

            and cache it for 50 mins!
        """
        cache_key = "token-for-%d" % installation.installation

        token = cache.get(cache_key)
        if not token:
            token = gh_app.get_access_token(installation.installation)
            token = token.token
            # token expires after 1 hr so cache it for 50 mins
            cache.set(cache_key, token, 3000)

        return token

    def _rpc_connection(self):
        # find AppInstallation on the current tenant
        installations = AppInstallation.objects.filter(tenant_pk=self.request.tenant.pk)

        # if there are more than 1 (usually on public) then try to find the installation
        # performed by the current user, e.g. on their own account
        if installations.count() > 1:
            social_user = self.request.user.social_auth.first()
            if social_user:
                installations = installations.filter(sender=social_user.uid)

        if installations.count() != 1:
            raise Exception('Cannot find GitHub App installation')

        installation = installations.first()

        gh_app = github.GithubIntegration(settings.KIWI_GITHUB_APP_ID,
                                          settings.KIWI_GITHUB_APP_PRIVATE_KEY)

        token = self._find_token(gh_app, installation)
        return github.Github(token)

    def is_adding_testcase_to_issue_disabled(self):
        """
            This integration is disabled only if there's no base_url!
        """
        return not self.bug_system.base_url
