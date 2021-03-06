# Generated by Django 3.0.4 on 2022-07-22 21:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('samples', '0161_powder_batch_stop_value_change'),
    ]

    operations = [
        migrations.AlterField(
            model_name='powderbatch',
            name='status',
            field=models.SmallIntegerField(choices=[(1000, 'Stop'), (0, 'Open'), (100, 'In Progress'), (200, 'Ready For Plate'), (300, 'Closed')], default=0, null=True),
        ),
    ]
