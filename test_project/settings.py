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
home_dir = os.path.expanduser("~")
removed_paths = []
for path in sys.path:
    if path.startswith(home_dir) and path.find('site-packages') == -1:
        removed_paths.append(path)

for path in removed_paths:
    sys.path.remove(path)

# re add them again
sys.path.extend(removed_paths)

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
with open(github_app_settings, "rb") as f:
    exec(  # pylint: disable=exec-used
        f.read(),
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

KIWI_GITHUB_APP_ID = 12345
KIWI_GITHUB_APP_PRIVATE_KEY = """
-----BEGIN RSA PRIVATE KEY-----
MIIEowIBAAKCAQEAtJFKoaSWDYpUvdjUaqW3Ft5p9O78rwJEBuJnEmmCPmZTz1tz
Hh2suPtWvolU/E1oOhbu0YPLHke0TC5uuBg5i5oA3b1UyfHdSiUYKmp0Mp9wkOpS
99pwtAA1sABjfDW6BPyo1Z+fs9V4gh89wNUFBkDO7hOqs01WNqomfQMTmmRQdt90
x0UpKQ8d6tBjov0C4oWBtsZiGQzMpoqQsaJNnIcfZjsSsrSbCUPTQmHWtdxfb1is
+dbwSczOeoBy6PcYasdVEF0PLOrw3hQ7XnY1Gx/MmexHdUPCGz13MjqtlxdXzxYl
TFDF97U+48f6vFleSXJKTNovtQ0F7IsW2H9uRwIDAQABAoIBABYtNf5OSYOWNrwu
UkBa4/ayEE9dvrj7zUEPM1uGi9GAHdD8yVGskVcSv1+dXEu0chWYVXJz/lFUuycU
GNMRXpfvrSWOqEg5JVWC4snq0ySYgmm57cC1GlxxHibklVNfAd607UN3XFTo5ekN
TzdMslZHRWLmFXP6DpmeIiX+Z7zxWjeCHnmtDj5npwAl0tJXuSKf9s7rxoiXKG2k
BAcmsBxU1/E2JflxSKuM1jxDo1q8B86lezHd3RY2xkDGMRY7DLlzVJW5euSw0S86
NnH/lh4Jzw/pq0Ev4MzNF6ypwCKWqdaqNBGc0YuFYafpZuqcHmW2OguDrXFqd4nG
oUfZqRECgYEA4LcXou2QmU771ib041yy/2sm3waMWaDwgewuYfhHPLqZtr3nx2kn
elFVO4miSwIAUQyMdMDx9YPa/4Nw2bUHAJqTTGsuU+Wulb3C9RjMeOPKyr2BQyMU
B1/f9TBY6l3qH+Z50hTAnlUtLc+qE5V/YKDGyJYq8NUw74KwR2/RXfkCgYEAzbTD
6ICR/gKpe725gJZbdZqjcrrUwDpaydwXXdqiC/vhwmj3b03F7aUGCjeXY0xSSmmg
bc2M0StoVOEZ6GJmoeVBrVSueS6AIwU9Fq9RoZNIgS+hBEs3hajDPM6ZMIbqORtW
rh9EfDnUxnRLOxXVqkVi1u2Ora5HPZ8fgfKvPj8CgYBQCgb6OmHJqW9b7M5G+Wqs
PU9AGwX8mq1vqV8v+A3vnItJosSeq16rW7LfHPvYeaMBO1X/9AV6rHdhkUCt2qPe
3C/hBUAgE+wmW8vIHwgdew1tPyh+cE0e/1A29fyFpePRbvcvE8Mz4iTQb2olxZb0
JPAI3Cv5UgY3GTaOi05oiQKBgQCzFT9FB8GRsQGZ77cyYjPnc6P+OvcDDwqBGDHj
jHZtFnEZzkYzyTKaTIOwm2sZkJVHoSOA1GVWqIKg+oOSkzAkm7EM1F88sqXtVx8y
w5i+oLmLdkqosU759s1Z/8bPv3TkGI/i8Oeveq1pxE7GdqDYJqYA1TnUrJfq5sAI
Yp38AwKBgBrNcGBQLrOXqmEJ0tYLg7DIoxvJrLvxtu2mbdohWS9rQFjkkA7+IsML
e6AQ/4uLtKdXZafgGSgqJ6tlB3J924Vb0HWmvnBcc2JCEPkgjuVDjXEMaqwIKjHa
a3C9rG6XtvAyGvIbXKI3tCNURbsjsgVwOgS6kESboZ576iDeH/eO
-----END RSA PRIVATE KEY-----""".strip()
