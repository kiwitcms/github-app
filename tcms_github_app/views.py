# Copyright (c) 2019 Alexander Todorov <atodorov@MrSenko.com>

# Licensed under the GPL 3.0: https://www.gnu.org/licenses/gpl-3.0.txt
# pylint: disable=unused-argument

import json

from django.conf import settings
from django.contrib import messages
from django.http import HttpResponse
from django.http import HttpResponseForbidden
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic.base import View

from tcms.utils import github

from tcms_github_app.models import AppInstallation
from tcms_github_app.models import WebhookPayload
from tcms_github_app import utils


class ApplicationEdit(View):
    """
        If there is an App installation made on GitHub by the current user
        then allow them to edit it.
    """
    def get(self, request, *args, **kwargs):
        social_user = request.user.social_auth.first()
        if not social_user:
            github_url = reverse('social:begin', args=['github'])
            messages.add_message(
                request,
                messages.WARNING,
                _(
                    'You have not logged-in via GitHub account! '
                    '<a href="%s">Click here</a>!') % github_url,
            )
            return HttpResponseRedirect('/')

        apps = AppInstallation.objects.filter(sender=social_user.uid)
        apps_count = apps.count()

        if apps_count == 0:  # pylint: disable=no-else-return
            github_url = 'https://github.com/apps/kiwi-tcms'
            messages.add_message(
                request,
                messages.WARNING,
                _(
                    'You have not installed Kiwi TCMS into your GitHub account! '
                    '<a href="%s">Click here</a>!' % github_url),
            )
            return HttpResponseRedirect('/')
        elif apps_count == 1:
            app_inst = apps.first()
            return HttpResponseRedirect(
                reverse('admin:tcms_github_app_appinstallation_change',
                        args=[app_inst.pk]))

        # multiple apps
        messages.add_message(
            request,
            messages.WARNING,
            _('Multiple GitHub App installations detected! See below:'),
        )

        for app_inst in apps:
            app_url = reverse('admin:tcms_github_app_appinstallation_change',
                              args=[app_inst.pk])
            messages.add_message(
                request,
                messages.WARNING,
                _('Edit GitHub App <a href="%s">%s</a>') % (app_url, app_inst),
            )
        return HttpResponseRedirect('/')


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
        elif payload.event == "create" and payload.payload.get('ref_type') == "tag":
            utils.create_version_from_tag(payload)

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
            action=payload.get('action'),
            sender=sender,
            payload=payload,
        )

        self.handle_payload(wh_payload)

        return HttpResponse('ok', content_type='text/plain')
