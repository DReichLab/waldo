# Generated by Django 3.0.4 on 2020-06-15 14:48

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('sequencing_run', '0016_remove_analysisfiles_pulldown_logfile_location'),
    ]

    operations = [
        migrations.AlterField(
            model_name='analysisfiles',
            name='created_by',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AlterField(
            model_name='analysisfiles',
            name='creation_timestamp',
            field=models.DateTimeField(default=django.utils.timezone.now, null=True),
        ),
        migrations.AlterField(
            model_name='analysisfiles',
            name='modification_timestamp',
            field=models.DateTimeField(default=django.utils.timezone.now, null=True),
        ),
        migrations.AlterField(
            model_name='analysisfiles',
            name='modified_by',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AlterField(
            model_name='mtanalysis',
            name='created_by',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AlterField(
            model_name='mtanalysis',
            name='creation_timestamp',
            field=models.DateTimeField(default=django.utils.timezone.now, null=True),
        ),
        migrations.AlterField(
            model_name='mtanalysis',
            name='modification_timestamp',
            field=models.DateTimeField(default=django.utils.timezone.now, null=True),
        ),
        migrations.AlterField(
            model_name='mtanalysis',
            name='modified_by',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AlterField(
            model_name='nuclearanalysis',
            name='created_by',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AlterField(
            model_name='nuclearanalysis',
            name='creation_timestamp',
            field=models.DateTimeField(default=django.utils.timezone.now, null=True),
        ),
        migrations.AlterField(
            model_name='nuclearanalysis',
            name='modification_timestamp',
            field=models.DateTimeField(default=django.utils.timezone.now, null=True),
        ),
        migrations.AlterField(
            model_name='nuclearanalysis',
            name='modified_by',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AlterField(
            model_name='shotgunanalysis',
            name='created_by',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AlterField(
            model_name='shotgunanalysis',
            name='creation_timestamp',
            field=models.DateTimeField(default=django.utils.timezone.now, null=True),
        ),
        migrations.AlterField(
            model_name='shotgunanalysis',
            name='modification_timestamp',
            field=models.DateTimeField(default=django.utils.timezone.now, null=True),
        ),
        migrations.AlterField(
            model_name='shotgunanalysis',
            name='modified_by',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AlterField(
            model_name='spikeanalysis',
            name='created_by',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AlterField(
            model_name='spikeanalysis',
            name='creation_timestamp',
            field=models.DateTimeField(default=django.utils.timezone.now, null=True),
        ),
        migrations.AlterField(
            model_name='spikeanalysis',
            name='modification_timestamp',
            field=models.DateTimeField(default=django.utils.timezone.now, null=True),
        ),
        migrations.AlterField(
            model_name='spikeanalysis',
            name='modified_by',
            field=models.CharField(blank=True, max_length=20),
        ),
    ]
