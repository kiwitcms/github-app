"""
    Migrates the `payload' field from the older
    django.contrib.postgres.JSONField type to the newer
    django.db.models.JSONField type.

    In Django 3.1.1 these are alias to the same field type
    and there shouldn't be any real changes to the underlying DB!
"""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tcms_github_app', '0002_appinstallation_settings_url'),
    ]

    operations = [
        migrations.AlterField(
            model_name='webhookpayload',
            name='payload',
            field=models.JSONField(),
        ),
    ]
