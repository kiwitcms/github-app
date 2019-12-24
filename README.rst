GitHub App integration for Kiwi TCMS
====================================

.. image:: https://travis-ci.org/kiwitcms/github-app.svg?branch=master
    :target: https://travis-ci.org/kiwitcms/github-app

.. image:: https://coveralls.io/repos/github/kiwitcms/github-app/badge.svg?branch=master
   :target: https://coveralls.io/github/kiwitcms/github-app?branch=master

.. image:: https://pyup.io/repos/github/kiwitcms/github-app/shield.svg
    :target: https://pyup.io/repos/github/kiwitcms/github-app/
    :alt: Python updates

.. image:: https://opencollective.com/kiwitcms/tiers/sponsor/badge.svg?label=sponsors&color=brightgreen
   :target: https://opencollective.com/kiwitcms#contributors
   :alt: Become a sponsor


Introduction
------------

This package provides the GitHub App integration for Kiwi TCMS and is
designed to work only for multi-tenant environments.
You don't need this add-on in order to run Kiwi TCMS without extended
GitHub integration!

Communication from GitHub to this add-on is via webhooks.

Add-on behavior:

- Auto-configure which tenant to use for database operations, either
  'public' or a single private tenant to which user has access.
- If unable to auto-configure display warning and redirect to configuration
  page once the GitHub account who installed this integration onto their
  GitHub repository logs into Kiwi TCMS
- Existing & newly created repositories are added as products in Kiwi TCMS.
  Fork repositories are skipped
- Newly created git tags are added as product versions in Kiwi TCMS
- 1-click bug reports to GitHub Issues


Vote for other ideas:

- When TE is updated then post status to pull request. See
  `Issue #9 <https://github.com/kiwitcms/github-app/issues/9>`_
- When opening PR then create a new TR. See
  `Issue #10 <https://github.com/kiwitcms/github-app/issues/10>`_
- When opening PR then auto-scan with kiwitcms-bot. See
  `Issue #11 <https://github.com/kiwitcms/github-app/issues/11>`_
- When new Tag/Release then perform artifact testing. See
  `Issue #12 <https://github.com/kiwitcms/github-app/issues/12>`_
- Auto-configure bug tracker for new product/repository. See
  `Issue #15 <https://github.com/kiwitcms/github-app/issues/15>`_


Installation
------------

::

    pip install kiwitcms-github-app

inside Kiwi TCMS's docker image and make sure the following settings are configured::

    MIDDLEWARE.append('tcms_github_app.middleware.CheckGitHubAppMiddleware')

everything else will be taken care for by Kiwi TCMS plugin loading code!


GitHub App configuration
------------------------

- User authorization callback URL: https://public.tenant.kiwitcms.org/complete/github/
- Request user authorization (OAuth) during installation - True
- Webhook URL - https://public.tenant.kiwitcms.org/kiwitcms_github_app/webhook/
- Permissions:

  - Contents: Read-only
  - Metadata: Read-only
  - Email addresses: Read-only

- Subscribe to events:

  - Meta
  - Create
  - Repository


Changelog
---------


v0.0.1 (24 Dec 2019)
~~~~~~~~~~~~~~~~~~~~

- initial release
