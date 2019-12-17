# Copyright (c) 2019 Alexander Todorov <atodorov@MrSenko.com>

# Licensed under the GPL 3.0: https://www.gnu.org/licenses/gpl-3.0.txt

from django.conf.urls import url
from tcms_github_app import views


urlpatterns = [
    url(r'^appedit/$', views.ApplicationEdit.as_view(), name='github_app_edit'),
    url(r'^webhook/$', views.WebHook.as_view(), name='github_app_webhook'),
]
