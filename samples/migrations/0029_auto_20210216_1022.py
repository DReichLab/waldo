# Generated by Django 3.0.4 on 2021-02-16 15:22

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('samples', '0028_period_culture_m2m_20210211_1543'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='sample',
            name='culture_fk',
        ),
        migrations.RemoveField(
            model_name='sample',
            name='period_fk',
        ),
    ]