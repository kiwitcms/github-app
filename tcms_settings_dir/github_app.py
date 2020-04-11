# Copyright (c) 2020 Alexander Todorov <atodorov@MrSenko.com>

# Licensed under the GPL 3.0: https://www.gnu.org/licenses/gpl-3.0.txt
# pylint: disable=undefined-variable

if 'tcms_github_app.middleware.CheckGitHubAppMiddleware' not in MIDDLEWARE:   # noqa: F821
    MIDDLEWARE.append('tcms_github_app.middleware.CheckGitHubAppMiddleware')  # noqa: F821

if 'tcms_github_app.views.WebHook' not in PUBLIC_VIEWS:   # noqa: F821
    PUBLIC_VIEWS.append('tcms_github_app.views.WebHook')  # noqa: F821
