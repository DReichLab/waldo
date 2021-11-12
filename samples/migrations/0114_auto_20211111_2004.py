# Generated by Django 3.0.4 on 2021-11-12 01:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('samples', '0113_copy_powder_batch_status'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='powderbatch',
            name='status',
        ),
        migrations.AlterField(
            model_name='powderbatch',
            name='status_int',
            field=models.SmallIntegerField(choices=[(-100, 'Stop'), (0, 'Open'), (100, 'In Progress'), (200, 'Ready For Plate')], default=0, null=True),
        ),
        migrations.DeleteModel(
            name='PowderBatchStatus',
        ),
    ]