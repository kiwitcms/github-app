# Copyright (c) 2019-2020 Alexander Todorov <atodorov@MrSenko.com>

# Licensed under the GPL 3.0: https://www.gnu.org/licenses/gpl-3.0.txt

from django import forms
from django.contrib import admin
from django.db.models import Q
from django.forms.utils import ErrorList
from django.http import HttpResponseForbidden
from django.http import HttpResponseRedirect
from django.utils.translation import gettext_lazy as _

from django_tenants.utils import get_tenant_model
from social_django.models import UserSocialAuth

from tcms_github_app import utils
from tcms_github_app.models import AppInstallation
from tcms_github_app.models import WebhookPayload


class WebhookPayloadAdmin(admin.ModelAdmin):
    list_display = ('pk', 'received_on', 'sender', 'event', 'action')
    ordering = ['-pk']

    @admin.options.csrf_protect_m
    def changelist_view(self, request, extra_context=None):
        if request.user.is_superuser:
            return super().changelist_view(request, extra_context)

        return HttpResponseForbidden('Unauthorized')

    def change_view(self, request, object_id, form_url='', extra_context=None):
        return HttpResponseForbidden()

    def has_change_permission(self, request, obj=None):
        return False

    def add_view(self, request, form_url='', extra_context=None):
        return HttpResponseForbidden()

    def has_add_permission(self, request):
        return False

    def delete_view(self, request, object_id, extra_context=None):
        return HttpResponseForbidden()

    def has_delete_permission(self, request, obj=None):
        return False


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
            tenants = UserSocialAuth.objects.get(
                provider='github-app',
                uid=instance.sender
            ).user.tenant_set.all()
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
    list_display = ('pk', 'installation', 'sender', 'tenant_pk', 'settings_url')
    ordering = ['-installation']

    form = AppInstallationChangeForm

    def has_change_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True

        if not obj:
            return False

        social_user = request.user.social_auth.first()
        if not social_user:
            return False

        return obj.sender == int(social_user.uid)

    def get_readonly_fields(self, request, obj=None):
        return ('installation', 'sender', 'settings_url')

    def get_fieldsets(self, request, obj=None):
        return [
            (None, {
                'fields': ('tenant_pk', 'installation', 'sender', 'settings_url'),
                'description': '<h1>' + _("""For additional configuration see
<a href="%s">GitHub</a>""") % obj.settings_url + '</h1>',
            }),
        ]

    def add_view(self, request, form_url='', extra_context=None):
        return HttpResponseForbidden()

    def has_add_permission(self, request):
        return False

    def delete_view(self, request, object_id, extra_context=None):
        return HttpResponseForbidden()

    def has_delete_permission(self, request, obj=None):
        return False

    @admin.options.csrf_protect_m
    def changelist_view(self, request, extra_context=None):
        if request.user.is_superuser:
            return super().changelist_view(request, extra_context)

        return HttpResponseForbidden()

    def response_change(self, request, obj):
        response = super().response_change(request, obj)
        if admin.options.IS_POPUP_VAR in request.POST:
            return response

        return HttpResponseRedirect('/')

    def save_form(self, request, form, change):
        app_inst = super().save_form(request, form, change)
        if form.has_changed() and app_inst.tenant_pk:
            utils.resync(request, app_inst)
        return app_inst


admin.site.register(WebhookPayload, WebhookPayloadAdmin)
admin.site.register(AppInstallation, AppInstallationAdmin)
