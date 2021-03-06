# Generated by Django 3.0.4 on 2021-10-29 02:58

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone

#choose non-empty fields, raise error if non-empty mismatch
def pick_best(existing, candidate):
	if existing is None or (isinstance(existing, str) and len(existing) == 0):
		return candidate
	elif candidate is not None:
		if isinstance(candidate, str):
			if len(candidate) > 0 and existing != candidate:
				raise ValueError(f'mismatch\texisting: "{existing}"\tcandidate: "{candidate}"')
		elif existing != candidate:
			raise ValueError(f'mismatch\texisting: "{existing}"\tcandidate: "{candidate}"')
	return existing

def populate_sequencing_runs(apps, source_type, destination_type, use_timestamps=False):
	source_model = apps.get_model('samples', source_type)
	destination_model = apps.get_model('samples', destination_type)
	for source in source_model.objects.all().order_by('date'):
		destination, created = destination_model.objects.get_or_create(name = source.name)
		
		destination.technician = pick_best(destination.technician, source.technician)
		destination.technician_fk = pick_best(destination.technician_fk, source.technician_fk)
		if destination.date is None:
			destination.date = source.date
		destination.sequencing = pick_best(destination.sequencing, source.sequencing)
		destination.notes = pick_best(destination.notes, source.notes)
		
		if use_timestamps:
			destination.creation_timestamp = source.creation_timestamp
			destination.created_by = source.created_by
			destination.modification_timestamp = source.modification_timestamp
			destination.modified_by = source.modified_by
		destination.save()

def combined_sequencing_runs(apps, schema_editor):
	destination = 'SequencingRun'
	populate_sequencing_runs(apps, 'NuclearSequencingRun', destination, True)
	populate_sequencing_runs(apps, 'ShotgunSequencingRun', destination)
	populate_sequencing_runs(apps, 'MTSequencingRun', destination)
	
def do_nothing(apps, schema_editor):
	pass

class Migration(migrations.Migration):

    dependencies = [
        ('samples', '0083_extractionprotocol_active'),
    ]

    operations = [
        migrations.CreateModel(
            name='SequencingRun',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('creation_timestamp', models.DateTimeField(default=django.utils.timezone.now, null=True)),
                ('created_by', models.CharField(blank=True, max_length=20)),
                ('modification_timestamp', models.DateTimeField(default=django.utils.timezone.now, null=True)),
                ('modified_by', models.CharField(blank=True, max_length=20)),
                ('name', models.CharField(db_index=True, max_length=50, unique=True)),
                ('technician', models.CharField(blank=True, default='', max_length=10)),
                ('date', models.DateField(null=True)),
                ('notes', models.TextField(blank=True, default='')),
                ('sequencing', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='samples.SequencingPlatform')),
                ('technician_fk', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='samples.WetLabStaff')),
            ],
            options={
                'abstract': False,
            },
        ),
		migrations.RunPython(combined_sequencing_runs, do_nothing),
    ]
