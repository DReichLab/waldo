# Generated by Django 3.0.4 on 2021-11-22 15:05

from django.db import migrations

def use_first_sequencing_platform_with_name(apps, queryset):
	SequencingRun = apps.get_model('samples', 'SequencingRun')
	SequencingPlatform = apps.get_model('samples', 'SequencingPlatform')
	
	for run in SequencingRun.objects.all():
		if run.sequencing:
			candidates = SequencingPlatform.objects.filter(platform=run.sequencing.platform).order_by('id')
			run.sequencing = candidates[0]
			run.save()

class Migration(migrations.Migration):

    dependencies = [
        ('samples', '0134_read_length_to_sequencing_run_from_platform'),
    ]

    operations = [
		migrations.RunPython(use_first_sequencing_platform_with_name),
    ]
