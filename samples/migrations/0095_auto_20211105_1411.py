# Generated by Django 3.0.4 on 2021-11-05 18:11

import django.core.validators
from django.db import migrations, models
import samples.models


class Migration(migrations.Migration):

    dependencies = [
        ('samples', '0094_libraryprotocol_active'),
    ]

    operations = [
        migrations.AlterField(
            model_name='nuclearcaptureplate',
            name='p5_index_start',
            field=models.PositiveSmallIntegerField(help_text='Must be odd in [1, 48]', null=True, validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(47), samples.models.validate_odd]),
        ),
    ]
