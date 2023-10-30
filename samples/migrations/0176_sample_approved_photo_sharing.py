# Generated by Django 3.0.3 on 2023-09-18 21:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('samples', '0175_barcode_index_reich_lab_default'),
    ]

    operations = [
        migrations.AddField(
            model_name='sample',
            name='approved_photo_sharing',
            field=models.BooleanField(help_text='Approved for sharing sample photographs. Null indicates unknown.', null=True),
        ),
    ]
