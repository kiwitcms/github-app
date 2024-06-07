# Copyright (c) 2020 Alexander Todorov <atodorov@otb.bg>
#
# Licensed under GNU Affero General Public License v3 or later (AGPLv3+)
# https://www.gnu.org/licenses/agpl-3.0.html

# pylint: disable=undefined-variable

if 'tcms_github_app.middleware.CheckGitHubAppMiddleware' not in MIDDLEWARE:   # noqa: F821
    MIDDLEWARE.append('tcms_github_app.middleware.CheckGitHubAppMiddleware')  # noqa: F821

if 'tcms_github_app.issues.Integration' not in EXTERNAL_BUG_TRACKERS:   # noqa: F821
    EXTERNAL_BUG_TRACKERS.append('tcms_github_app.issues.Integration')  # noqa: F821
