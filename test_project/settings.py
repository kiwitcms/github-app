# Copyright (c) 2019 Alexander Todorov <atodorov@MrSenko.com>

# Licensed under the GPL 3.0: https://www.gnu.org/licenses/gpl-3.0.txt

import os
from tcms.settings.product import *

# these are enabled only for testing purposes
DEBUG = True
TEMPLATE_DEBUG = True
SECRET_KEY = '7d09f358-6609-11e9-8140-34363b8604e2'
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
LOCALE_PATHS = [os.path.join(BASE_DIR, 'tcms_github_app', 'locale')]


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': '/tmp/test_project.sqlite',
    }
}

INSTALLED_APPS.extend([
    'social_django',
    'tcms_github_app',
])

PUBLIC_VIEWS.extend([
    'tcms_github_app.views.WebHook'
])


ROOT_URLCONF = 'test_project.urls'

# application specific configuration
# NOTE: must be bytes, not string
KIWI_GITHUB_APP_SECRET = b'S3cr3t'
