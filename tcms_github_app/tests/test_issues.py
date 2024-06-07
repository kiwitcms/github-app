# Copyright (c) 2023-2024 Alexander Todorov <atodorov@otb.bg>
#
# Licensed under GNU Affero General Public License v3 or later (AGPLv3+)
# https://www.gnu.org/licenses/agpl-3.0.html

# pylint: disable=attribute-defined-outside-init

import os
import time
import unittest

from django.http import HttpRequest
from django.utils import timezone
from parameterized import parameterized

from tcms.testcases.models import BugSystem
from tcms.tests.factories import ComponentFactory, TestExecutionFactory

from tcms_github_app.issues import Integration
from tcms_github_app.tests import AppInstallationFactory, LoggedInTestCase


@unittest.skipUnless(
    os.getenv("KIWI_GITHUB_APP_ID") and os.getenv("KIWI_GITHUB_APP_PRIVATE_KEY"),
    "Testing environment not configured",
)
class TestGitHubIntegration(LoggedInTestCase):
    public_bug_url = "https://github.com/kiwitcms/test-github-integration/issues/1"
    private_bug_url = "https://github.com/kiwitcms/private-test-github-integration/issues/1"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.execution_1 = TestExecutionFactory()
        cls.execution_1.case.summary = "kiwitcms-github-app at " + timezone.now().isoformat()
        cls.execution_1.case.text = "Given-When-Then"
        cls.execution_1.case.save()  # will generate history object
        cls.execution_1.run.summary = (
            "Automated TR for GitHub integration on " + timezone.now().isoformat()
        )
        cls.execution_1.run.save()

        cls.component = ComponentFactory(
            name="GitHub integration", product=cls.execution_1.build.version.product
        )
        cls.execution_1.case.add_component(cls.component)

        AppInstallationFactory(
            installation=6185099,
            sender=1002300,
            tenant_pk=cls.tenant.pk
        )

        # simulate a tenant request for bugtracker integration class
        request = HttpRequest()
        request.META['HTTP_HOST'] = cls.tenant.get_primary_domain().domain
        request.tenant = cls.tenant

        public_bug_system = BugSystem.objects.create(  # nosec:B106:hardcoded_password_funcarg
            name="App integration for kiwitcms/test-github-integration",
            tracker_type="tcms_github_app.issues.Integration",
            base_url="https://github.com/kiwitcms/test-github-integration",
        )
        cls.public_tracker = Integration(public_bug_system, request)

        private_bug_system = BugSystem.objects.create(  # nosec:B106:hardcoded_password_funcarg
            name="App integration for kiwitcms/private-test-github-integration",
            tracker_type="tcms_github_app.issues.Integration",
            base_url="https://github.com/kiwitcms/private-test-github-integration",
        )
        cls.private_tracker = Integration(private_bug_system, request)

    def test_details_for_public_url(self):
        result = self.public_tracker.details(self.public_bug_url)

        self.assertEqual("Hello GitHub", result["title"])
        self.assertEqual(
            "This issue is used in automated tests that verify Kiwi TCMS - GitHub "
            "bug tracking integration!",
            result["description"],
        )

    def test_details_for_private_url(self):
        result = self.private_tracker.details(self.private_bug_url)

        self.assertEqual("Hello Private GitHub", result["title"])
        self.assertEqual(
            "This issue is used in automated tests that verify "
            "Kiwi TCMS - GitHub bug tracking integration!",
            result["description"],
        )

    @parameterized.expand(
        [
            ("public",),
            ("private",),
        ]
    )
    def test_auto_update_bugtracker(self, name):
        tracker = getattr(self, f"{name}_tracker")
        bug_url = getattr(self, f"{name}_bug_url")

        repo_id = tracker.repo_id
        repo = tracker.rpc.get_repo(repo_id)
        issue = repo.get_issue(1)

        # make sure there are no comments to confuse the test
        initial_comments_count = 0
        for comment in issue.get_comments():
            initial_comments_count += 1
            self.assertNotIn(self.execution_1.run.summary, comment.body)

        # simulate user adding a new bug URL to a TE and clicking
        # 'Automatically update bug tracker'
        tracker.add_testexecution_to_issue([self.execution_1], bug_url)

        # wait until comments have been refreshed b/c this seem to happen async
        retries = 0
        last_comment = None
        current_comment_count = 0
        while current_comment_count <= initial_comments_count:
            current_comment_count = 0
            # .get_comments() returns an iterator
            for comment in issue.get_comments():
                current_comment_count += 1
                last_comment = comment

            time.sleep(1)
            retries += 1
            self.assertLess(retries, 20)

        # reporter was kiwi-tcms (the app)
        self.assertEqual(last_comment.user.login, "kiwi-tcms[bot]")

        # assert that a comment has been added as the last one
        # and also verify its text
        for expected_string in [
            "Confirmed via test execution",
            f"TR-{self.execution_1.run_id}: {self.execution_1.run.summary}",
            self.execution_1.run.get_full_url(),
            f"TE-{self.execution_1.pk}: {self.execution_1.case.summary}",
        ]:
            self.assertIn(expected_string, last_comment.body)

        # clean up after ourselves in case everything above looks good
        last_comment.delete()

    @parameterized.expand(
        [
            ("public_tracker",),
            ("private_tracker",),
        ]
    )
    def test_report_issue_from_test_execution_1click(self, name):
        tracker = getattr(self, name)

        # simulate user clicking the 'Report bug' button in TE widget, TR page
        url = tracker.report_issue_from_testexecution(self.execution_1, self.tester)

        self.assertIn(tracker.bug_system.base_url, url)
        self.assertIn("/issues/", url)

        new_issue_id = tracker.bug_id_from_url(url)
        repo_id = tracker.repo_id
        repo = tracker.rpc.get_repo(repo_id)
        issue = repo.get_issue(new_issue_id)

        # reporter was kiwi-tcms (the app)
        self.assertEqual("kiwi-tcms[bot]", issue.user.login)

        self.assertEqual(f"Failed test: {self.execution_1.case.summary}", issue.title)
        for expected_string in [
            f"Filed from execution {self.execution_1.get_full_url()}",
            "Reporter",
            self.execution_1.build.version.product.name,
            self.component.name,
            "Steps to reproduce",
            self.execution_1.case.text,
        ]:
            self.assertIn(expected_string, issue.body)

        # close issue after we're done
        issue.edit(state="closed")
