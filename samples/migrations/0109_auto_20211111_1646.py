# Generated by Django 3.0.4 on 2021-11-11 21:46

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('samples', '0108_remove_mt_capture_plate_and_shotgun_pool'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='NuclearCapturePlate',
            new_name='CaptureOrShotgunPlate',
        ),
    ]
