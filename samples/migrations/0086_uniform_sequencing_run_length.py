# Generated by Django 3.0.4 on 2021-10-29 22:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('samples', '0085_sequencing_run_references'),
    ]

    operations = [
        migrations.AlterField(
            model_name='mtsequencingrun',
            name='name',
            field=models.CharField(max_length=50),
        ),
    ]