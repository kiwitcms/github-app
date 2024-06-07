# Copyright (c) 2019-2020 Alexander Todorov <atodorov@otb.bg>
#
# Licensed under GNU Affero General Public License v3 or later (AGPLv3+)
# https://www.gnu.org/licenses/agpl-3.0.html

from django.urls import include, path

from tcms.urls import urlpatterns


urlpatterns += [
    path('', include('social_django.urls', namespace='social')),
]
