# Generated by Django 3.0.4 on 2021-11-05 17:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('samples', '0093_librarybatch_control_set'),
    ]

    operations = [
        migrations.AddField(
            model_name='libraryprotocol',
            name='active',
            field=models.BooleanField(default=True),
        ),
    ]