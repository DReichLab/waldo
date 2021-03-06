# Generated by Django 3.0.4 on 2021-11-22 02:19

from django.db import migrations

def copy_lanes_of_sequencing_from_sequencing_platform_to_sequencing_run(apps, queryset):
	SequencingRun = apps.get_model('samples', 'SequencingRun')
	for run in SequencingRun.objects.all():
		sequencing_platform = run.sequencing
		if sequencing_platform:
			run.lanes_sequenced = int(sequencing_platform.lanes_runs)
			run.save()

class Migration(migrations.Migration):

    dependencies = [
        ('samples', '0130_default_open_capture_status'),
    ]

    operations = [
		migrations.RunPython(copy_lanes_of_sequencing_from_sequencing_platform_to_sequencing_run),
    ]
