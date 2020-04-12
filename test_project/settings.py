# Copyright (c) 2019 Alexander Todorov <atodorov@MrSenko.com>
#
# Licensed under the GPL 3.0: https://www.gnu.org/licenses/gpl-3.0.txt
#
# pylint: disable=invalid-name,protected-access,wrong-import-position
# pylint: disable=wildcard-import, unused-wildcard-import

import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
# site-packages/tcms_settings_dir/ must be before ./tcms_settings_dir/
# so we can load multi_tenant.py first!
if BASE_DIR in sys.path:
    sys.path.remove(BASE_DIR)
    sys.path.append(BASE_DIR)

import pkg_resources

# pretend this is a plugin during testing & development
# IT NEEDS TO BE BEFORE the wildcard import below !!!
# .egg-info/ directory will mess up with this
dist = pkg_resources.Distribution(__file__)
entry_point = pkg_resources.EntryPoint.parse('kiwitcms_github_app = tcms_github_app',
                                             dist=dist)
dist._ep_map = {'kiwitcms.plugins': {'kiwitcms_github_app': entry_point}}
pkg_resources.working_set.add(dist)

from tcms.settings.product import *  # noqa: F403

# check for a clean devel environment
if os.path.exists(os.path.join(BASE_DIR, "kiwitcms_github_app.egg-info")):
    print("ERORR: .egg-info/ directories mess up plugin loading code in devel mode")
    sys.exit(1)

# import the settings which automatically get distributed with this package
github_app_settings = os.path.join(
    BASE_DIR, 'tcms_settings_dir', 'github_app.py')

# Kiwi TCMS loads extra settings in the same way using exec()
exec(  # pylint: disable=exec-used
    open(github_app_settings, "rb").read(),
    globals()
)

# these are enabled only for testing purposes
DEBUG = True
TEMPLATE_DEBUG = True
SECRET_KEY = '7d09f358-6609-11e9-8140-34363b8604e2'


DATABASES['default'].update({  # pylint: disable=objects-update-used
    'NAME': 'test_project',
    'USER': 'kiwi',
    'PASSWORD': 'kiwi',
    'HOST': 'localhost',
    'OPTIONS': {},
})


INSTALLED_APPS.append('social_django')
ROOT_URLCONF = 'test_project.urls'


# Allows serving non-public tenants on a sub-domain
# WARNING: doesn't work well when you have a non-standard port-number
KIWI_TENANTS_DOMAIN = 'tenants.localdomain'


# application specific configuration
# NOTE: must be bytes, not string
KIWI_GITHUB_APP_SECRET = b'S3cr3t'
