# Generated by Django 3.0.4 on 2020-05-25 12:02

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('samples', '0012_auto_20200522_1808'),
    ]

    operations = [
        migrations.RenameField(
            model_name='extractionprotocol',
            old_name='reference_abbreviation',
            new_name='manuscript_summary',
        ),
        migrations.RenameField(
            model_name='supportstaff',
            old_name='late_name',
            new_name='last_name',
        ),
        migrations.RenameField(
            model_name='wetlabstaff',
            old_name='late_name',
            new_name='last_name',
        ),
    ]