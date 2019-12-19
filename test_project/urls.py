# Copyright (c) 2019 Alexander Todorov <atodorov@MrSenko.com>

# Licensed under the GPL 3.0: https://www.gnu.org/licenses/gpl-3.0.txt

from django.conf.urls import include, url

from tcms.urls import urlpatterns
from tcms_tenants import urls as tenants_urls


urlpatterns += [
    url(r'^tenants/', include(tenants_urls, namespace='tenants')),
    url('', include('social_django.urls', namespace='social')),
]
