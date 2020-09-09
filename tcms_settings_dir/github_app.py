# Copyright (c) 2020 Alexander Todorov <atodorov@MrSenko.com>

# Licensed under the GPL 3.0: https://www.gnu.org/licenses/gpl-3.0.txt
# pylint: disable=undefined-variable

if 'tcms_github_app.middleware.CheckGitHubAppMiddleware' not in MIDDLEWARE:   # noqa: F821
    MIDDLEWARE.append('tcms_github_app.middleware.CheckGitHubAppMiddleware')  # noqa: F821

if 'tcms_github_app.issues.Integration' not in EXTERNAL_BUG_TRACKERS:   # noqa: F821
    EXTERNAL_BUG_TRACKERS.append('tcms_github_app.issues.Integration')  # noqa: F821
