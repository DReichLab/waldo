# Generated by Django 3.0.4 on 2020-05-21 18:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('samples', '0009_auto_20200520_1736'),
    ]

    operations = [
        migrations.AlterField(
            model_name='extractionprotocol',
            name='name',
            field=models.CharField(max_length=150),
        ),
        migrations.AlterField(
            model_name='librarybatch',
            name='name',
            field=models.CharField(blank=True, max_length=150),
        ),
        migrations.AlterField(
            model_name='mtcaptureprotocol',
            name='name',
            field=models.CharField(max_length=150),
        ),
        migrations.AlterField(
            model_name='nuclearcaptureprotocol',
            name='name',
            field=models.CharField(max_length=150),
        ),
    ]
