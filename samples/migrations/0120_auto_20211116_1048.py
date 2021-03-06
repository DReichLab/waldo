# Generated by Django 3.0.4 on 2021-11-16 15:48

from django.db import migrations, models
import samples.validation


class Migration(migrations.Migration):

    dependencies = [
        ('samples', '0119_sequencingrun_captures'),
    ]

    operations = [
        migrations.AlterField(
            model_name='captureorshotgunplate',
            name='needs_sequencing',
            field=models.BooleanField(default=True, help_text='True for new plates. False for plates sequenced before website switchover.'),
        ),
        migrations.AlterField(
            model_name='captureprotocol',
            name='name',
            field=models.CharField(max_length=150, unique=True, validators=[samples.validation.validate_no_whitespace, samples.validation.validate_no_underscore]),
        ),
    ]
