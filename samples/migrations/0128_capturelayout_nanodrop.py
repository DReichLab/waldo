# Generated by Django 3.0.4 on 2021-11-21 03:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('samples', '0127_controllayout_notes'),
    ]

    operations = [
        migrations.AddField(
            model_name='capturelayout',
            name='nanodrop',
            field=models.DecimalField(decimal_places=2, max_digits=5, null=True),
        ),
    ]
