# Generated by Django 2.1.7 on 2019-05-01 17:47

from django.db import migrations

# move from one flowcell to multiple flowcells for a SequencingAnalysisRun and its resulting DemultiplexedSequencing

def many_flowcells_analysis_runs(apps, schema_editor):
	SequencingAnalysisRun = apps.get_model('sequencing_run', 'SequencingAnalysisRun')
	for run in SequencingAnalysisRun.objects.all():
		if run.triggering_flowcell != None:
			run.triggering_flowcells.add(run.triggering_flowcell)
			run.save()
	
def many_flowcells_demultiplexed_sequencing(apps, schema_editor):
	DemultiplexedSequencing = apps.get_model('sequencing_run', 'DemultiplexedSequencing')
	for sequencing in DemultiplexedSequencing.objects.all():
		sequencing.flowcells.add(sequencing.flowcell)
		sequencing.save()

class Migration(migrations.Migration):

    dependencies = [
        ('sequencing_run', '0006_auto_20190501_1338'),
    ]

    operations = [
		migrations.RunPython(many_flowcells_analysis_runs),
		migrations.RunPython(many_flowcells_demultiplexed_sequencing)
    ]