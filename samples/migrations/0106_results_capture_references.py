# Generated by Django 3.0.4 on 2021-11-11 21:06

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('samples', '0105_merge_captures'),
    ]

    operations = [
        migrations.AddField(
            model_name='results',
            name='mt_capture_plate_temp',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='results_mt', to='samples.NuclearCapturePlate'),
        ),
        migrations.AddField(
            model_name='results',
            name='shotgun_plate',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='results_shotgun', to='samples.NuclearCapturePlate'),
        ),
        migrations.AlterField(
            model_name='results',
            name='nuclear_capture_plate',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='results_nuclear', to='samples.NuclearCapturePlate'),
        ),
    ]
