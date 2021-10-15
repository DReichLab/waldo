# Generated by Django 3.0.4 on 2021-10-15 22:58

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('samples', '0068_library_protocol_udg_and_library_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='librarybatch',
            name='p7_offset',
            field=models.SmallIntegerField(null=True, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(47)]),
        ),
        migrations.AlterField(
            model_name='librarybatch',
            name='prep_date',
            field=models.DateField(help_text='YYYY-MM-DD', null=True),
        ),
    ]
