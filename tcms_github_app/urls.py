# Copyright (c) 2019-2020 Alexander Todorov <atodorov@otb.bg>
#
# Licensed under GNU Affero General Public License v3 or later (AGPLv3+)
# https://www.gnu.org/licenses/agpl-3.0.html

from django.urls import re_path
from tcms_github_app import views


urlpatterns = [
    re_path(r'^appedit/$', views.ApplicationEdit.as_view(), name='github_app_edit'),
    re_path(r'^resync/$', views.Resync.as_view(), name='github_app_resync'),
    re_path(r'^webhook/$', views.WebHook.as_view(), name='github_app_webhook'),
]
