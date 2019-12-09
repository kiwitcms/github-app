# Copyright (c) 2019 Alexander Todorov <atodorov@MrSenko.com>

# Licensed under the GPL 3.0: https://www.gnu.org/licenses/gpl-3.0.txt

from django.conf.urls import include, url

from tcms.urls import urlpatterns
from tcms_github_app import urls


urlpatterns += [
    url(r'^github/app/', include(urls)),
]
