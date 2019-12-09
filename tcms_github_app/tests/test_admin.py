# Copyright (c) 2019 Alexander Todorov <atodorov@MrSenko.com>

# Licensed under the GPL 3.0: https://www.gnu.org/licenses/gpl-3.0.txt
# pylint: disable=too-many-ancestors

from django.urls import reverse
from django.conf import settings
from django.http import HttpResponseForbidden

from tcms_github_app.models import WebhookPayload
from tcms_github_app.tests import LoggedInTestCase


class PurchaseAdminTestCase(LoggedInTestCase):
    def tearDown(self):
        self.tester.is_superuser = False
        self.tester.save()

    def test_changelist_unauthorized_for_regular_user(self):
        response = self.client.get(
            reverse('admin:tcms_github_app_webhookpayload_changelist'))
        self.assertIsInstance(response, HttpResponseForbidden)
        self.assertIn('Unauthorized', str(response.content,
                                          encoding=settings.DEFAULT_CHARSET))

    def test_changelist_authorized_for_superuser(self):
        # create an object so we can use its values to validate
        # the changelist view
        payload = WebhookPayload.objects.create(
            action='test-admin-changelist-view',
            sender=self.tester.username,
            payload={},
        )

        self.tester.is_superuser = True
        self.tester.save()

        response = self.client.get(
            reverse('admin:tcms_github_app_webhookpayload_changelist'))

        # assert all columns that must be visible
        self.assertContains(response, payload.pk)
        self.assertContains(response, payload.action)
        self.assertContains(response, payload.sender)
        # timestamps are formatted according to localization
        self.assertContains(response, 'Received on')

    def test_add_not_possible(self):
        response = self.client.get(
            reverse('admin:tcms_github_app_webhookpayload_add'))
        self.assertRedirects(
            response,
            reverse('admin:tcms_github_app_webhookpayload_changelist'),
            fetch_redirect_response=False,
        )

    def test_delete_not_possible(self):
        # create an object so we can use its PK to resolve the
        # delete view, otherwise Django will tell us that we are trying
        # to delete a non-existing object
        payload = WebhookPayload.objects.create(
            action='test-admin-delete-view',
            sender=self.tester.username,
            payload={},
        )

        response = self.client.get(
            reverse('admin:tcms_github_app_webhookpayload_delete',
                    args=[payload.pk])
        )
        self.assertRedirects(
            response,
            reverse('admin:tcms_github_app_webhookpayload_changelist'),
            fetch_redirect_response=False,
        )
