# Copyright (c) 2020-2024 Alexander Todorov <atodorov@MrSenko.com>
#
# Licensed under the GPL 3.0: https://www.gnu.org/licenses/gpl-3.0.txt
#

import github
from django.conf import settings

from tcms.issuetracker.types import GitHub

from tcms_github_app import utils


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
    def _rpc_connection(self):
        installations = utils.find_installations(self.request)

        if installations.count() != 1:
            raise RuntimeError(
                f'Cannot find GitHub App installation for tenant "{self.request.tenant.name}"')

        installation = installations.first()

        gh_app = github.GithubIntegration(
            auth=github.Auth.AppAuth(settings.KIWI_GITHUB_APP_ID,
                                     settings.KIWI_GITHUB_APP_PRIVATE_KEY),
        )

        token = utils.find_token_from_app_inst(gh_app, installation)
        return github.Github(auth=github.Auth.Token(token))

    def is_adding_testcase_to_issue_disabled(self):
        """
            This integration is disabled only if there's no base_url!
        """
        return not self.bug_system.base_url
