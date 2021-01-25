GitHub App integration for Kiwi TCMS
====================================

.. image:: https://coveralls.io/repos/github/kiwitcms/github-app/badge.svg?branch=master
   :target: https://coveralls.io/github/kiwitcms/github-app?branch=master

.. image:: https://pyup.io/repos/github/kiwitcms/github-app/shield.svg
    :target: https://pyup.io/repos/github/kiwitcms/github-app/
    :alt: Python updates

.. image:: https://tidelift.com/badges/package/pypi/kiwitcms-github-app
    :target: https://tidelift.com/subscription/pkg/pypi-kiwitcms-github-app?utm_source=pypi-kiwitcms-github-app&utm_medium=github&utm_campaign=readme
    :alt: Tidelift

.. image:: https://opencollective.com/kiwitcms/tiers/sponsor/badge.svg?label=sponsors&color=brightgreen
   :target: https://opencollective.com/kiwitcms#contributors
   :alt: Become a sponsor

.. image:: https://img.shields.io/twitter/follow/KiwiTCMS.svg
    :target: https://twitter.com/KiwiTCMS
    :alt: Kiwi TCMS on Twitter


Introduction
------------

This package provides the GitHub App integration for
`Kiwi TCMS Enterprise <https://github.com/MrSenko/kiwitcms-enterprise/>`_
and is designed to work only for multi-tenant environments!
You don't need this add-on in order to run Kiwi TCMS without extended
GitHub integration!

Communication from GitHub to this plugin is via webhooks.

Plugin behavior:

- Auto-configure which tenant to use for database operations, either
  'public' or a single private tenant to which user has access.
- If unable to auto-configure display warning and redirect to configuration
  page once the GitHub account who installed this integration onto their
  GitHub repository logs into Kiwi TCMS
- Existing & newly created repositories are added as products in Kiwi TCMS
- BugSystem records are automatically configured for repositories
- Fork repositories are skipped
- Newly created git tags are added as product versions in Kiwi TCMS


See `Issues <https://github.com/kiwitcms/github-app/issues>`_ for other ideas!


Installation
------------

::

    pip install kiwitcms-github-app

inside Kiwi TCMS's docker image and make sure the following settings are configured::

    AUTHENTICATION_BACKENDS = [
        'social_core.backends.github.GithubAppAuth',
        ...
    ]
    SOCIAL_AUTH_GITHUB_APP_KEY = 'xxxxxx'
    SOCIAL_AUTH_GITHUB_APP_SECRET = 'yyy'
    KIWI_GITHUB_APP_SECRET = b'your-webhook-secret'
    KIWI_GITHUB_APP_ID = 123456
    KIWI_GITHUB_APP_PRIVATE_KEY = """-----BEGIN RSA PRIVATE KEY-----
    +++++++++base64-encoded-private-key+++++++
    -----END RSA PRIVATE KEY-----"""

everything else will be taken care for by Kiwi TCMS plugin loading code!


GitHub App configuration
------------------------

This plugin needs an existing GitHub App application with the following
configuration:

- User authorization callback URL: https://tcms.example.com/complete/github-app/
- Request user authorization (OAuth) during installation - True
- Webhook Active - True
- Webhook URL - https://tcms.example.com/kiwitcms_github_app/webhook/
- Webhook Secret - <the value of KIWI_GITHUB_APP_SECRET>
- SSL verification - Enabled

Then configure how the application interacts with GitHub:

- Repository permissions:

  - Contents: Read-only
  - Issues: Read & write (required for 1-click bug report on private repos)
  - Metadata: Read-only

- User permissions:

  - Email addresses: Read-only

- Subscribe to events:

  - Meta
  - Create
  - Repository


Changelog
---------

v1.2.3 (25 Jan 2021)
~~~~~~~~~~~~~~~~~~~~

- Allow POST request (web hooks) without CSRF token


v1.2.2 (08 Dec 2020)
~~~~~~~~~~~~~~~~~~~~

- Update for newer PyGithub


v1.2.1 (17 Sep 2020)
~~~~~~~~~~~~~~~~~~~~

- Require login for views.Resync()


v1.2 (13 Sep 2020)
~~~~~~~~~~~~~~~~~~

- Adjusted to work with Django 3.1 and Kiwi TCMS > 8.6
- Replace deprecated ``url()`` with ``re_path()``
- Migrate the ``payload`` field to newer ``models.JSONField`` type
- Setting ``PUBLIC_VIEWS`` is removed in Kiwi TCMS so remove the
  automatic adjustment
- Make error messages for missing AppInst more clear
- Remove redundant if condition in Resync()
- Update translation strings
- Update documentation around GitHub permission requirements for
  1-click bug report


v1.1 (05 Aug 2020)
~~~~~~~~~~~~~~~~~~

- Add GitHub issue-tracker integration which authenticates as the installed app.
  Fixes `Issue #25 <https://github.com/kiwitcms/github-app/issues/25>`_
- Configure BugSystem for new repos. Fixes
  `Issue #15 <https://github.com/kiwitcms/github-app/issues/15>`_
- Create Product & BugSystem records when installation_repositores change.
  Fixes `Issue #21 <https://github.com/kiwitcms/github-app/issues/21>`_
- Trigger resync from GitHub via menu. Fixes
  `Issue #19 <https://github.com/kiwitcms/github-app/issues/19>`_
- Trigger resync from GitHub after AppInstallation is configured. Fixes
  `Issue #20 <https://github.com/kiwitcms/github-app/issues/20>`_
- Database: Add ``AppInstallation.settings_url`` field
- Link to the correct URL for GitHub settings. Fixes
  `Issue #33 <https://github.com/kiwitcms/github-app/issues/33>`_
- Require user to be logged in for ApplicationEdit. Fixes
  `Issue #36 <https://github.com/kiwitcms/github-app/issues/36>`_
- Update translation strings
- Add more tests


v1.0 (13 Apr 2020)
~~~~~~~~~~~~~~~~~~

- Install settings overrides under ``tcms_settings_dir/``
  (compatible with Kiwi TCMS v8.2 or later):

  - does not need ``MIDDLEWARE`` and ``PUBLIC_VIEWS`` override anymore
- Remove ``GithubAppAuth`` backend, shipped with social-auth-core v3.3.0
- Fix a redirect to use the correct name of our social_core backend


v0.0.5 (19 Feb 2020)
~~~~~~~~~~~~~~~~~~~~

- Address GitHub API deprecation not yet fixed in social-auth-core


v0.0.4 (25 Dec 2019)
~~~~~~~~~~~~~~~~~~~~

- Do not fail if product already exists
- Do not fail if repository doesn't have description
- Search UserSocialAuth by uid and provider


v0.0.1 (24 Dec 2019)
~~~~~~~~~~~~~~~~~~~~

- initial release
