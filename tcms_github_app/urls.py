# Copyright (c) 2019-2020 Alexander Todorov <atodorov@MrSenko.com>

# Licensed under the GPL 3.0: https://www.gnu.org/licenses/gpl-3.0.txt

from django.urls import re_path
from tcms_github_app import views


urlpatterns = [
    re_path(r'^appedit/$', views.ApplicationEdit.as_view(), name='github_app_edit'),
    re_path(r'^resync/$', views.Resync.as_view(), name='github_app_resync'),
    re_path(r'^webhook/$', views.WebHook.as_view(), name='github_app_webhook'),
]
