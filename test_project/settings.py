# Copyright (c) 2019 Alexander Todorov <atodorov@MrSenko.com>

# Licensed under the GPL 3.0: https://www.gnu.org/licenses/gpl-3.0.txt

from tcms.settings.product import *

# these are enabled only for testing purposes
DEBUG = True
TEMPLATE_DEBUG = True
SECRET_KEY = '7d09f358-6609-11e9-8140-34363b8604e2'


##### start multi-tenant settings override
DATABASES['default'].update({
    'ENGINE': 'django_tenants.postgresql_backend',
    'NAME': 'test_project',
    'USER': 'kiwi',
    'PASSWORD': 'kiwi',
    'HOST': 'localhost',
    'OPTIONS': {},
})

DATABASE_ROUTERS = [
    'django_tenants.routers.TenantSyncRouter',
]


MIDDLEWARE.insert(0, 'django_tenants.middleware.main.TenantMainMiddleware')
MIDDLEWARE.append('tcms_tenants.middleware.BlockUnauthorizedUserMiddleware')

TENANT_MODEL = "tcms_tenants.Tenant"
TENANT_DOMAIN_MODEL = "tcms_tenants.Domain"

INSTALLED_APPS.insert(0, 'django_tenants')
INSTALLED_APPS.insert(1, 'tcms_tenants')

INSTALLED_APPS.extend([
    'social_django',
    'tcms_github_app',
])

PUBLIC_VIEWS.extend([
    'tcms_github_app.views.WebHook'
])

TENANT_APPS = [
    'django.contrib.sites',

    'attachments',
    'django_comments',
    'modernrpc',
    'simple_history',

    'tcms.bugs',
    'tcms.core.contrib.linkreference',
    'tcms.management',
    'tcms.testcases.apps.AppConfig',
    'tcms.testplans.apps.AppConfig',
    'tcms.testruns.apps.AppConfig',
]

# everybody can access the main instance
SHARED_APPS = INSTALLED_APPS

# Allows serving non-public tenants on a sub-domain
# WARNING: doesn't work well when you have a non-standard port-number
KIWI_TENANTS_DOMAIN = 'tenants.localdomain'

# share login session between tenants
SESSION_COOKIE_DOMAIN = ".%s" % KIWI_TENANTS_DOMAIN

# main navigation menu
MENU_ITEMS.append(
    (_('TENANT'), [
        (_('Create'), reverse_lazy('tcms_tenants:create-tenant')),
        ('-', '-'),
        (_('Authorized users'), '/admin/tcms_tenants/tenant_authorized_users/'),
    ]),
)

# attachments storage
DEFAULT_FILE_STORAGE = "tcms_tenants.storage.TenantFileSystemStorage"
MULTITENANT_RELATIVE_MEDIA_ROOT = "tenants/%s"


ROOT_URLCONF = 'test_project.urls'

# application specific configuration
# NOTE: must be bytes, not string
KIWI_GITHUB_APP_SECRET = b'S3cr3t'
