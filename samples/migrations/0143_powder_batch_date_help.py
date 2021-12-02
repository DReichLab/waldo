# Generated by Django 3.0.4 on 2021-12-02 18:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('samples', '0142_close_old_powder_batches'),
    ]

    operations = [
        migrations.AlterField(
            model_name='powderbatch',
            name='date',
            field=models.DateField(help_text='Date batch was powdered: YYYY-MM-DD', null=True),
        ),
    ]
