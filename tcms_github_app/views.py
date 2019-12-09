# Copyright (c) 2019 Alexander Todorov <atodorov@MrSenko.com>

# Licensed under the GPL 3.0: https://www.gnu.org/licenses/gpl-3.0.txt

import json
from datetime import datetime

from django.conf import settings
from django.urls import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.views.generic.base import View, TemplateView
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.decorators import login_required

from tcms.utils import github

from tcms_github_app.models import Installation


# pylint: disable=unused-argument
class WebHook(View):
    """
        Handles `marketplace_purchase` web hook as described at:
        https://developer.github.com/marketplace/listing-on-github-marketplace/configuring-the-github-marketplace-webhook/
    """
    http_method_names = ['post', 'head', 'options']

    def post(self, request, *args, **kwargs):
        """
            Hook must be configured to receive JSON payload!

            Save the 'purchased' event in the database, see:
            https://developer.github.com/marketplace/integrating-with-the-github-marketplace-api/github-marketplace-webhook-events/
        """
        result = github.verify_signature(
            request, settings.KIWI_GITHUB_MARKETPLACE_SECRET)
        if result is not True:
            return result  # must be an HttpResponse then

        payload = json.loads(request.body.decode('utf-8'))

        # ping hook https://developer.github.com/webhooks/#ping-event
        if 'zen' in payload:
            return HttpResponse('pong', content_type='text/plain')

        # format is 2017-10-25T00:00:00+00:00
        effective_date = datetime.strptime(payload['effective_date'][:19],
                                           '%Y-%m-%dT%H:%M:%S')
        # save payload for future use
        purchase = Purchase.objects.create(
            vendor='github',
            action=payload['action'],
            sender=payload['sender']['email'],
            effective_date=effective_date,
            payload=payload,
        )
        organization = utils.organization_from_purchase(purchase)

        # plan cancellations must be handled here
        if purchase.action == 'cancelled':
            return utils.cancel_plan(purchase)

        if purchase.action == 'purchased':
            # recurring billing events don't redirect to Install URL
            # they only send a web hook
            tenant = Tenant.objects.filter(
                owner__email=purchase.sender,
                organization=organization,
                paid_until__isnull=False,
            ).first()
            if tenant:
                tenant.paid_until = utils.calculate_paid_until(
                    purchase.payload['marketplace_purchase'],
                    purchase.effective_date,
                )
                tenant.save()

        return HttpResponse('ok', content_type='text/plain')
