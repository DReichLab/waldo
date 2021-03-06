# Generated by Django 2.0.3 on 2018-04-03 17:34

from django.db import migrations
from django.core.exceptions import ObjectDoesNotExist

# sequencing run analyses existing at this point should have only one name
def set_single_sample_name(apps, schema_editor):
	SequencingAnalysisRun = apps.get_model('sequencing_run', 'SequencingAnalysisRun')
	SequencingRunID = apps.get_model('sequencing_run', 'SequencingRunID')
	OrderedSequencingRunID = apps.get_model('sequencing_run', 'OrderedSequencingRunID')
	for sequencing_analysis_run in SequencingAnalysisRun.objects.all():
		try:
			name_object_to_add = SequencingRunID.objects.get(name=sequencing_analysis_run.name)
			ordered_sequencing_run_id = OrderedSequencingRunID.objects.create(sequencing_analysis_run=sequencing_analysis_run, name=name_object_to_add, interface_order=0)
		except ObjectDoesNotExist:
			print("{} does not exist as sequencing run ID".format(sequencing_analysis_run.name))

class Migration(migrations.Migration):

	dependencies = [
		('sequencing_run', '0003_auto_20180403_1734'),
		]

	operations = [
		migrations.RunPython(set_single_sample_name)
	]
