# Generated by Django 3.0.4 on 2021-10-27 11:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('samples', '0082_remove_redundant_layout_names'),
    ]

    operations = [
        migrations.AddField(
            model_name='extractionprotocol',
            name='active',
            field=models.BooleanField(default=True),
        ),
    ]
