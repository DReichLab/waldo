# Generated by Django 3.0.4 on 2021-11-08 03:32

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('samples', '0099_copy_protocol_references'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='mtcaptureplate',
            name='protocol',
        ),
        migrations.RemoveField(
            model_name='nuclearcaptureplate',
            name='protocol',
        ),
        migrations.DeleteModel(
            name='MTCaptureProtocol',
        ),
        migrations.DeleteModel(
            name='NuclearCaptureProtocol',
        ),
    ]