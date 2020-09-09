# Copyright (c) 2019-2020 Alexander Todorov <atodorov@MrSenko.com>
#
# Licensed under the GPL 3.0: https://www.gnu.org/licenses/gpl-3.0.txt

from django.urls import include, path

from tcms.urls import urlpatterns


urlpatterns += [
    path('', include('social_django.urls', namespace='social')),
]
