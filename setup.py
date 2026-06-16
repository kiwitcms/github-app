# Copyright (c) 2019-2026 Alexander Todorov <atodorov@otb.bg>
#
# Licensed under GNU Affero General Public License v3 or later (AGPLv3+)
# https://www.gnu.org/licenses/agpl-3.0.html

# pylint: disable=missing-docstring

from setuptools import setup, find_packages


def get_long_description():
    with open('README.rst', 'r', encoding="utf-8") as file:
        return file.read()


def get_install_requires(path):
    requires = []

    with open(path, 'r', encoding="utf-8") as file:
        for line in file:
            if line.startswith('-r '):
                continue
            requires.append(line.strip())
        return requires


setup(
    name='kiwitcms-github-app',
    version='2.2.2',
    description='GitHub App integration for Kiwi TCMS',
    long_description=get_long_description(),
    author='Kiwi TCMS',
    author_email='info@kiwitcms.org',
    url='https://github.com/kiwitcms/github-app/',
    license='AGPLv3+',
    install_requires=get_install_requires('requirements.txt'),
    python_requires='>=3.12',
    packages=find_packages(exclude=['test_project*', '*.tests']),
    zip_safe=False,
    include_package_data=True,
    classifiers=[
        'Framework :: Django',
        'Development Status :: 5 - Production/Stable',
        'Topic :: Software Development :: Quality Assurance',
        'Topic :: Software Development :: Testing',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.12',
        'Framework :: Django :: 6.0',
    ],
    entry_points={"kiwitcms.plugins": ["kiwitcms_github_app = tcms_github_app"]},
)
