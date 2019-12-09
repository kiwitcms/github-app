# Copyright (c) 2019 Alexander Todorov <atodorov@MrSenko.com>

# Licensed under the GPL 3.0: https://www.gnu.org/licenses/gpl-3.0.txt

import json

from django.conf import settings
from django.http import HttpResponse, HttpResponseForbidden
from django.views.generic.base import View

from tcms.utils import github
from tcms_github_app.models import WebhookPayload
from tcms_github_app import utils


# pylint: disable=unused-argument
class WebHook(View):
    """
        Handles `marketplace_purchase` web hook as described at:
        https://developer.github.com/marketplace/listing-on-github-marketplace/configuring-the-github-marketplace-webhook/
    """
    http_method_names = ['post', 'head', 'options']

    @staticmethod
    def handle_payload(payload):
        if payload.event == "repository" and payload.action == "created":
            utils.create_product_from_repository(payload)
        elif payload.event == "installation" and payload.action == "created":
            utils.create_installation(payload)

    def post(self, request, *args, **kwargs):
        """
            Hook must be configured to receive JSON payload!
        """
        result = github.verify_signature(
            request, settings.KIWI_GITHUB_APP_SECRET)

        if result is not True:
            return result  # must be an HttpResponse then

        event = request.headers.get('X-GitHub-Event', None)
        if not event:
            return HttpResponseForbidden('Missing event')

        payload = json.loads(request.body.decode('utf-8'))

        # ping hook https://developer.github.com/webhooks/#ping-event
        if 'zen' in payload:
            return HttpResponse('pong', content_type='text/plain')

        # GitHub ID will be matched again UserSocialAuth.uid
        sender = payload['sender']['id']

        wh_payload = WebhookPayload.objects.create(
            event=event,
            action=payload['action'],
            sender=sender,
            payload=payload,
        )

        self.handle_payload(wh_payload)

        return HttpResponse('ok', content_type='text/plain')
