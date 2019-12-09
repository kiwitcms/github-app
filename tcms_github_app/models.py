# Copyright (c) 2019 Alexander Todorov <atodorov@MrSenko.com>

# Licensed under the GPL 3.0: https://www.gnu.org/licenses/gpl-3.0.txt

from django.db import models
from django.contrib.postgres.fields import JSONField
from django.contrib.postgres.indexes import GinIndex


class Installation(models.Model):
    """
        Holds information about GitHub App installation events:
    """
    action = models.CharField(max_length=64, db_index=True)
    sender = models.EmailField(db_index=True)
    effective_date = models.DateTimeField(db_index=True)

    # this is for internal purposes
    received_on = models.DateTimeField(db_index=True, auto_now_add=True)

    payload = JSONField()

    class Meta:
        indexes = [
            GinIndex(fastupdate=False,
                     fields=['payload'],
                     name='tcms_github_payload_gin'),
        ]

    def __str__(self):
        return "Purchase %s from %s on %s" % (self.action,
                                              self.sender,
                                              self.received_on.isoformat())
