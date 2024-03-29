# Generated by Django 3.0.4 on 2022-09-06 22:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('samples', '0162_auto_20220722_1719'),
    ]

    operations = [
        migrations.AddField(
            model_name='sample',
            name='approved_negative_results',
            field=models.BooleanField(default=False, help_text='Approved for full reporting of negative results and photographs'),
        ),
    ]
