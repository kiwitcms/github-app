# Copyright (c) 2019-2022 Alexander Todorov <atodorov@otb.bg>
#
# Licensed under GNU Affero General Public License v3 or later (AGPLv3+)
# https://www.gnu.org/licenses/agpl-3.0.html

# pylint: disable=invalid-name, avoid-auto-field

import django.contrib.postgres.fields.jsonb
import django.contrib.postgres.indexes
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='WebhookPayload',
            fields=[
                ('id', models.AutoField(auto_created=True,
                                        primary_key=True,
                                        serialize=False,
                                        verbose_name='ID')),
                ('event', models.CharField(db_index=True, max_length=64)),
                ('action', models.CharField(db_index=True, max_length=64, null=True, blank=True)),
                ('sender', models.PositiveIntegerField(db_index=True)),
                ('received_on', models.DateTimeField(auto_now_add=True,
                                                     db_index=True)),
                ('payload', django.contrib.postgres.fields.jsonb.JSONField()),
            ],
        ),
        migrations.AddIndex(
            model_name='webhookpayload',
            index=django.contrib.postgres.indexes.GinIndex(
                fastupdate=False,
                fields=['payload'],
                name='tcms_github_app_payload_gin'),
        ),
        migrations.CreateModel(
            name='AppInstallation',
            fields=[
                ('id', models.AutoField(auto_created=True,
                                        primary_key=True,
                                        serialize=False,
                                        verbose_name='ID')),
                ('installation', models.PositiveIntegerField(db_index=True)),
                ('sender', models.PositiveIntegerField(db_index=True)),
                ('tenant_pk', models.PositiveIntegerField(db_index=True,
                                                          null=True,
                                                          blank=True)),
            ],
        ),
    ]
