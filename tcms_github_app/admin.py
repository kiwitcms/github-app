# Copyright (c) 2019 Alexander Todorov <atodorov@MrSenko.com>

# Licensed under the GPL 3.0: https://www.gnu.org/licenses/gpl-3.0.txt

from django.urls import reverse
from django.contrib import admin
from django.http import HttpResponseForbidden, HttpResponseRedirect

from tcms_github_marketplace.models import Purchase


class PurchaseAdmin(admin.ModelAdmin):
    list_display = ('pk', 'vendor', 'action', 'sender',
                    'effective_date', 'received_on')
    ordering = ['-pk']

    def add_view(self, request, form_url='', extra_context=None):
        return HttpResponseRedirect(
            reverse('admin:tcms_github_marketplace_purchase_changelist'))

    @admin.options.csrf_protect_m
    def changelist_view(self, request, extra_context=None):
        if request.user.is_superuser:
            return super().changelist_view(request, extra_context)

        return HttpResponseForbidden('Unauthorized')

    @admin.options.csrf_protect_m
    def delete_view(self, request, object_id, extra_context=None):
        return HttpResponseRedirect(
            reverse('admin:tcms_github_marketplace_purchase_changelist'))


admin.site.register(Purchase, PurchaseAdmin)
