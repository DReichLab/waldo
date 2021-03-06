# Generated by Django 3.0.4 on 2021-11-07 22:31

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('samples', '0097_merge_capture_protocols'),
    ]

    operations = [
        migrations.AddField(
            model_name='mtcaptureplate',
            name='protocol_temp',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to='samples.CaptureProtocol'),
        ),
        migrations.AddField(
            model_name='nuclearcaptureplate',
            name='protocol_temp',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to='samples.CaptureProtocol'),
        ),
    ]
