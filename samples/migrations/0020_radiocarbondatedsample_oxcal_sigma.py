# Generated by Django 3.0.4 on 2020-12-14 20:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('samples', '0019_auto_20201203_1815'),
    ]

    operations = [
        migrations.AddField(
            model_name='radiocarbondatedsample',
            name='oxcal_sigma',
            field=models.FloatField(null=True),
        ),
    ]
