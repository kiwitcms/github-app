# Copyright (c) 2019 Alexander Todorov <atodorov@MrSenko.com>

# Licensed under the GPL 3.0: https://www.gnu.org/licenses/gpl-3.0.txt

from tcms.settings.product import *

# these are enabled only for testing purposes
DEBUG = True
TEMPLATE_DEBUG = True
SECRET_KEY = '7d09f358-6609-11e9-8140-34363b8604e2'


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'test_project',
        'USER': 'kiwi',
        'PASSWORD': 'kiwi',
        'HOST': 'localhost',
        'OPTIONS': {},
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
