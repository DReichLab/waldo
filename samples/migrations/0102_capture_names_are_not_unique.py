# Generated by Django 3.0.4 on 2021-11-10 15:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('samples', '0101_auto_20211107_2237'),
    ]

    operations = [
        migrations.AlterField(
            model_name='nuclearcaptureplate',
            name='name',
            field=models.CharField(max_length=50),
        ),
    ]
