# Generated by Django 3.0.4 on 2021-07-30 19:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('samples', '0048_auto_20210730_1520'),
    ]

    operations = [
        migrations.AlterField(
            model_name='extractbatch',
            name='batch_name',
            field=models.CharField(max_length=50, unique=True),
        ),
    ]
