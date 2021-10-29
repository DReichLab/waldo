# Generated by Django 3.0.4 on 2021-10-29 17:35

from django.db import migrations, models
import django.db.models.deletion

# There are not separate sequencing runs for MT, shotgun, and nuclear data. 
# Each sequencing run may have only some of this data for any given sample, but this changes references to treat them as the same type of object.
def results_sequencing_run_references(apps, schema_editor):
	Results = apps.get_model('samples', 'Results')
	SequencingRun = apps.get_model('samples', 'SequencingRun')
	
	for results in Results.objects.all():
		mt = results.mt_seq_run
		if mt is not None:
			results.mt_seq_run_temp = SequencingRun.objects.get(name=mt.name)
		
		shotgun = results.shotgun_seq_run
		if shotgun is not None:
			results.shotgun_seq_run_temp = SequencingRun.objects.get(name=shotgun.name)
		
		nuclear = results.nuclear_seq_run
		if nuclear is not None:
			results.nuclear_seq_run_temp = SequencingRun.objects.get(name=nuclear.name)
		
		results.save()
		
def do_nothing(apps, schema_editor):
	pass

class Migration(migrations.Migration):

    dependencies = [
        ('samples', '0084_sequencingrun'),
    ]

    operations = [
        migrations.AddField(
            model_name='results',
            name='mt_seq_run_temp',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='results_mt', to='samples.SequencingRun'),
        ),
        migrations.AddField(
            model_name='results',
            name='nuclear_seq_run_temp',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='results_nuclear', to='samples.SequencingRun'),
        ),
        migrations.AddField(
            model_name='results',
            name='shotgun_seq_run_temp',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='results_shotgun', to='samples.SequencingRun'),
        ),
		migrations.RunPython(results_sequencing_run_references, do_nothing),
    ]
