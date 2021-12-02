# Generated by Django 3.0.4 on 2021-12-01 18:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('samples', '0138_null_well_positions'),
    ]

    operations = [
        migrations.AlterField(
            model_name='powderbatch',
            name='status',
            field=models.SmallIntegerField(choices=[(-100, 'Stop'), (0, 'Open'), (100, 'In Progress'), (200, 'Ready For Plate'), (300, 'Closed')], default=0, null=True),
        ),
    ]
