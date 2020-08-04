from django.db import migrations, models


def forward_settings_url(apps, schema_editor):
    """
        # copy the URL from the actual GitHub payload and update existing records
    """
    webhookpayload_model = apps.get_model('tcms_github_app', 'WebHookPayload')
    appinstallation_model = apps.get_model('tcms_github_app', 'AppInstallation')

    for app_inst in appinstallation_model.objects.all():
        install_hook = webhookpayload_model.objects.filter(
            sender=app_inst.sender, event="installation", action="created"
        ).first()
        if install_hook:
            app_inst.settings_url = install_hook.payload['installation']['html_url']
            app_inst.save()


def reverse_settings_url(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('tcms_github_app', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='appinstallation',
            name='settings_url',
            field=models.URLField(blank=True, null=True),
        ),

        migrations.RunPython(forward_settings_url, reverse_settings_url),
    ]
