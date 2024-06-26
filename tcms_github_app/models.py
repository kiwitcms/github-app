# Copyright (c) 2019-2021 Alexander Todorov <atodorov@otb.bg>
#
# Licensed under GNU Affero General Public License v3 or later (AGPLv3+)
# https://www.gnu.org/licenses/agpl-3.0.html

from django.db import models
from django.contrib.postgres.indexes import GinIndex


class WebhookPayload(models.Model):
    """
        Holds information about received webhooks
    """
    event = models.CharField(max_length=64, db_index=True)
    action = models.CharField(max_length=64, db_index=True, null=True, blank=True)
    # GitHub UID, match with UserSocialAuth.uid
    sender = models.PositiveIntegerField(db_index=True)

    # this is for internal purposes
    received_on = models.DateTimeField(db_index=True, auto_now_add=True)
    payload = models.JSONField()

    class Meta:
        indexes = [
            GinIndex(fastupdate=False,
                     fields=['payload'],
                     name='tcms_github_app_payload_gin'),
        ]

    def __str__(self):
        return (
            f"WebhookPayload '{self.action}' from '{self.sender}'"
            f" on '{self.received_on.isoformat()}'"
        )


class AppInstallation(models.Model):
    """
        Holds information for which tenant is this GitHub installation
        authorized. Everything is integers instead of FK to allow
        installation before/after a user is logged into Kiwi TCMS and
        allow for GitHub admins/users leaving organizations, leaving Kiwi TCMS, etc.

        The overriden admin interface is where the magic happens!
    """
    installation = models.PositiveIntegerField(db_index=True)
    sender = models.PositiveIntegerField(db_index=True)
    # None - means unconfigured tenant, otherwise has value
    tenant_pk = models.PositiveIntegerField(null=True, blank=True, db_index=True)
    settings_url = models.URLField(null=True, blank=True)

    def __str__(self):
        return f"GitHub App {self.installation}"
