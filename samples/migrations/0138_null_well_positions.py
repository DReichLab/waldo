# Generated by Django 3.0.4 on 2021-12-01 15:34

import django.core.validators
from django.db import migrations, models
import samples.layout


class Migration(migrations.Migration):

    dependencies = [
        ('samples', '0137_auto_20211122_1542'),
    ]

    operations = [
        migrations.AlterField(
            model_name='capturelayout',
            name='column',
            field=models.PositiveSmallIntegerField(null=True, validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(12)]),
        ),
        migrations.AlterField(
            model_name='capturelayout',
            name='row',
            field=models.CharField(max_length=1, null=True, validators=[samples.layout.validate_row_letter]),
        ),
        migrations.AlterField(
            model_name='controllayout',
            name='column',
            field=models.PositiveSmallIntegerField(null=True, validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(12)]),
        ),
        migrations.AlterField(
            model_name='controllayout',
            name='row',
            field=models.CharField(max_length=1, null=True, validators=[samples.layout.validate_row_letter]),
        ),
        migrations.AlterField(
            model_name='extractionbatchlayout',
            name='column',
            field=models.PositiveSmallIntegerField(null=True, validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(12)]),
        ),
        migrations.AlterField(
            model_name='extractionbatchlayout',
            name='row',
            field=models.CharField(max_length=1, null=True, validators=[samples.layout.validate_row_letter]),
        ),
        migrations.AlterField(
            model_name='librarybatchlayout',
            name='column',
            field=models.PositiveSmallIntegerField(null=True, validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(12)]),
        ),
        migrations.AlterField(
            model_name='librarybatchlayout',
            name='row',
            field=models.CharField(max_length=1, null=True, validators=[samples.layout.validate_row_letter]),
        ),
        migrations.AlterField(
            model_name='lysatebatchlayout',
            name='column',
            field=models.PositiveSmallIntegerField(null=True, validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(12)]),
        ),
        migrations.AlterField(
            model_name='lysatebatchlayout',
            name='row',
            field=models.CharField(max_length=1, null=True, validators=[samples.layout.validate_row_letter]),
        ),
    ]
