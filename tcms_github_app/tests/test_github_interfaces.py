# Copyright (c) 2023 Alexander Todorov <atodorov@MrSenko.com>

# Licensed under the GPL 3.0: https://www.gnu.org/licenses/gpl-3.0.txt
# pylint: disable=invalid-name

import inspect
import unittest

import github
from tcms_github_app import issues, utils


class PyGithubInterfaces(unittest.TestCase):
    """
    The upstream github.Github class has a history of changing its parameters
    relatively frequesntly, not always in a backwards compatible way!
    """
    def test_utils_PatchedGithub_and_upstream_Github_should_have_the_same_signature(self):
        signature_for_downstream_github = inspect.signature(utils.PatchedGithub)
        signature_for_upstream_github = inspect.signature(github.Github)

        self.assertEqual(signature_for_downstream_github, signature_for_upstream_github)

    def test_issues_GithubKiwiTCMSBot_and_upstream_Github_should_have_the_same_signature(self):
        signature_for_downstream_github = inspect.signature(issues.GithubKiwiTCMSBot)
        signature_for_upstream_github = inspect.signature(github.Github)

        self.assertEqual(signature_for_downstream_github, signature_for_upstream_github)

    def test_instantiate_an_object_from_utils_PatchedGithub_class(self):
        utils.PatchedGithub("testing-token")

    def test_instantiate_an_object_from_issues_GithubKiwiTCMSBot_class(self):
        issues.GithubKiwiTCMSBot("testing-token")
