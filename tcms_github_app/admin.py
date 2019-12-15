# Copyright (c) 2019 Alexander Todorov <atodorov@MrSenko.com>

# Licensed under the GPL 3.0: https://www.gnu.org/licenses/gpl-3.0.txt

from django import forms
from django.contrib import admin
from django.db.models import Q
from django.forms.utils import ErrorList
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.http import HttpResponseForbidden, HttpResponseRedirect

from django_tenants.utils import get_tenant_model
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


class AppInstallationChangeForm(forms.ModelForm):
    # As a security concern we would like to have this queryset set to
    # Tenant.objects.none() instead of .all(). However ModelChoiceField.to_python()
    # is trying to self.queryset.get() the currently selected value! When the queryset
    # is empty this raises ValidationError!
    # The internal mechanics of this are in BaseForm._clean_fields()::L399(Django 2.1.7)
    # which calls field.clean(value) before any clean_<field_name>() methods on the form!
    tenant_pk = forms.ModelChoiceField(
        queryset=get_tenant_model().objects.all(),
        required=False
    )

    def __init__(self,  # pylint: disable=too-many-arguments
                 data=None, files=None, auto_id='id_%s', prefix=None,
                 initial=None, error_class=ErrorList, label_suffix=None,
                 empty_permitted=False, instance=None, use_required_attribute=None,
                 renderer=None):
        super().__init__(data, files, auto_id, prefix,
                         initial, error_class, label_suffix,
                         empty_permitted, instance, use_required_attribute,
                         renderer)
        if instance:
            # passed by ModelAdmin._chageform_view():L1581 when changing existing object
            tenants = UserSocialAuth.objects.get(uid=instance.sender).user.tenant_set.all()
            self.fields['tenant_pk'].queryset = get_tenant_model().objects.filter(
                Q(schema_name='public') | Q(pk__in=tenants),
            )
        else:
            self.fields['tenant_pk'].queryset = self.fields['tenant_pk'].queryset.none()

    def clean_tenant_pk(self):
        """
            Secial-case tenant_pk field because
            ModelChoiceField returns objects, not int!
        """
        tenant = self.cleaned_data['tenant_pk']
        if tenant:
            return tenant.pk

        return None


class AppInstallationAdmin(admin.ModelAdmin):
    list_display = ('pk', 'installation', 'sender', 'tenant_pk')
    ordering = ['-installation']

    form = AppInstallationChangeForm

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

    def get_fieldsets(self, request, obj=None):
        return [
            (None, {
                'fields': ('tenant_pk', 'installation', 'sender'),
                'description': '<h1>' + _("""For additional configuration see
<a href="https://github.com/settings/installations/%d">GitHub</a>""") % obj.installation + '</h1>',
            }),
        ]


admin.site.register(WebhookPayload, WebhookPayloadAdmin)
admin.site.register(AppInstallation, AppInstallationAdmin)
