# Generated by Django 3.0.4 on 2021-11-12 00:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('samples', '0111_sequencingplatform_active'),
    ]

    operations = [
        migrations.AddField(
            model_name='powderbatch',
            name='status_int',
            field=models.SmallIntegerField(null=True),
        ),
    ]
