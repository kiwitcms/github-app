# Copyright (c) 2019-2024 Alexander Todorov <atodorov@otb.bg>
#
# Licensed under GNU Affero General Public License v3 or later (AGPLv3+)
# https://www.gnu.org/licenses/agpl-3.0.html

# pylint: disable=too-few-public-methods

from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from tcms_github_app.models import AppInstallation


class CheckGitHubAppMiddleware:
    """
        Warns the user and redirects them to configure their GitHub App
        installation so it knows on which tenant to create new objects in DB.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.user.is_authenticated or request.method != "GET":
            return self.get_response(request)

        tenant = getattr(request, "tenant")
        if not tenant or tenant.owner != request.user:
            return self.get_response(request)

        app_inst = None
        social_user = request.user.social_auth.filter(provider='github-app').first()
        if social_user:
            app_inst = AppInstallation.objects.filter(
                sender=social_user.uid,
                tenant_pk=None
            ).first()

        if app_inst:
            admin_path = reverse('admin:tcms_github_app_appinstallation_change',
                                 args=[app_inst.pk])
            if request.path != admin_path:
                messages.add_message(
                    request,
                    messages.WARNING,
                    _('Unconfigured GitHub App %d') % app_inst.installation,
                    fail_silently=True)
                return HttpResponseRedirect(admin_path)

        return self.get_response(request)
