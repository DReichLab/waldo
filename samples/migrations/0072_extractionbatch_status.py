# Generated by Django 3.0.4 on 2021-10-18 15:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('samples', '0071_lysatebatch_status_default_open'),
    ]

    operations = [
        migrations.AddField(
            model_name='extractionbatch',
            name='status',
            field=models.PositiveSmallIntegerField(choices=[(0, 'Open'), (1, 'Extracted')], default=0),
        ),
    ]