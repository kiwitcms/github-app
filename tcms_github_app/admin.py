# Copyright (c) 2019 Alexander Todorov <atodorov@MrSenko.com>

# Licensed under the GPL 3.0: https://www.gnu.org/licenses/gpl-3.0.txt

from django.urls import reverse
from django.contrib import admin
from django.http import HttpResponseForbidden, HttpResponseRedirect

from social_django.models import UserSocialAuth

from tcms_github_app.models import AppInstallation
from tcms_github_app.models import WebhookPayload


class WebhookPayloadAdmin(admin.ModelAdmin):
    list_display = ('pk', 'received_on', 'sender', 'event', 'action')
    ordering = ['-pk']

    def add_view(self, request, form_url='', extra_context=None):
        return HttpResponseRedirect(
            reverse('admin:tcms_github_app_webhookpayload_changelist'))

    @admin.options.csrf_protect_m
    def changelist_view(self, request, extra_context=None):
        if request.user.is_superuser:
            return super().changelist_view(request, extra_context)

        return HttpResponseForbidden('Unauthorized')

    @admin.options.csrf_protect_m
    def delete_view(self, request, object_id, extra_context=None):
        return HttpResponseRedirect(
            reverse('admin:tcms_github_app_webhookpayload_changelist'))


class AppInstallationAdmin(admin.ModelAdmin):
    list_display = ('pk', 'installation', 'sender', 'tenant_pk')
    ordering = ['-installation']

    def has_change_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True

        if not obj:
            return False

        social_user = UserSocialAuth.objects.filter(user=request.user).first()
        if not social_user:
            return False

        return obj.sender == int(social_user.uid)

    def get_readonly_fields(self, request, obj=None):
        return ('installation', 'sender')


admin.site.register(WebhookPayload, WebhookPayloadAdmin)
admin.site.register(AppInstallation, AppInstallationAdmin)
