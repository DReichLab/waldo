# Generated by Django 3.0.4 on 2020-12-02 20:12

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('samples', '0016_auto_20200629_1433'),
    ]

    operations = [
        migrations.CreateModel(
            name='RadiocarbonCalibration',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('creation_timestamp', models.DateTimeField(default=django.utils.timezone.now, null=True)),
                ('created_by', models.CharField(blank=True, max_length=20)),
                ('modification_timestamp', models.DateTimeField(default=django.utils.timezone.now, null=True)),
                ('modified_by', models.CharField(blank=True, max_length=20)),
                ('program', models.CharField(blank=True, max_length=30)),
                ('version', models.CharField(blank=True, max_length=30)),
                ('curve', models.CharField(blank=True, max_length=30)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='radiocarbondatedsample',
            name='cal_from',
            field=models.IntegerField(null=True),
        ),
        migrations.AddField(
            model_name='radiocarbondatedsample',
            name='cal_to',
            field=models.IntegerField(null=True),
        ),
        migrations.AddField(
            model_name='radiocarbondatedsample',
            name='correction_applied',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='radiocarbondatedsample',
            name='first_publication',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to='samples.Publication'),
        ),
        migrations.AddField(
            model_name='radiocarbondatedsample',
            name='oxcal_mu',
            field=models.FloatField(null=True),
        ),
        migrations.AddField(
            model_name='radiocarbondatedsample',
            name='calibration',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to='samples.RadiocarbonCalibration'),
        ),
    ]
