# Generated by Django 3.0.4 on 2021-10-17 20:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('samples', '0069_library_batch_p7_offset_and_date_help'),
    ]

    operations = [
        migrations.AddField(
            model_name='lysatebatch',
            name='status',
            field=models.PositiveSmallIntegerField(choices=[(0, 'Open'), (1, 'Lysates created')], default=1),
        ),
    ]
