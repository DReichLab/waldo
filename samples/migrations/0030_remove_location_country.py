# Generated by Django 3.0.4 on 2021-02-16 16:25

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('samples', '0029_auto_20210216_1022'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='location',
            name='country',
        ),
    ]