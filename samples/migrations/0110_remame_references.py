# Generated by Django 3.0.4 on 2021-11-11 21:59

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('samples', '0109_auto_20211111_1646'),
    ]

    operations = [
        migrations.RenameField(
            model_name='captureorshotgunplate',
            old_name='protocol_temp',
            new_name='protocol',
        ),
        migrations.RenameField(
            model_name='results',
            old_name='mt_capture_plate_temp',
            new_name='mt_capture_plate',
        ),
    ]
