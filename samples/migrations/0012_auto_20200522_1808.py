# Generated by Django 3.0.4 on 2020-05-22 22:08

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('samples', '0011_auto_20200522_1801'),
    ]

    operations = [
        migrations.RenameField(
            model_name='libraryprotocol',
            old_name='library_method_reference_abbreviation',
            new_name='manuscript_summary',
        ),
        migrations.RenameField(
            model_name='mtcaptureprotocol',
            old_name='publication_summary',
            new_name='protocol_reference',
        ),
    ]
