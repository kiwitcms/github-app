# Copyright (c) 2023-2024 Alexander Todorov <atodorov@otb.bg>
#
# Licensed under GNU Affero General Public License v3 or later (AGPLv3+)
# https://www.gnu.org/licenses/agpl-3.0.html

# pylint: disable=invalid-name, protected-access

import inspect
import unittest

import github
from tcms_github_app import utils


class PyGithubInterfaces(unittest.TestCase):
    """
    The upstream github.Github class has a history of changing its parameters
    relatively frequesntly, not always in a backwards compatible way!
    """
    def test_utils_PatchedGithub_and_upstream_Github_should_have_the_same_signature(self):
        signature_for_downstream_github = inspect.signature(utils.PatchedGithub)
        signature_for_upstream_github = inspect.signature(github.Github)

        self.assertEqual(signature_for_downstream_github, signature_for_upstream_github)

    def test_instantiate_an_object_from_utils_PatchedGithub_class(self):
        inst = utils.PatchedGithub(auth=github.Auth.Token("testing-token"))
        self.assertIsNotNone(inst._Github__requester)  # pylint: disable=no-member

        inst = github.Github(auth=github.Auth.Token("testing-token"))
        self.assertIsNotNone(inst._Github__requester)
