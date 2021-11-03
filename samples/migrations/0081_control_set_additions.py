# Generated by Django 3.0.4 on 2021-10-25 18:27

from django.db import migrations, models
import django.db.models.deletion

def control_sets_from_existing_layouts(apps, schema_editor):
	ControlSet = apps.get_model('samples', 'ControlSet')
	ControlLayout = apps.get_model('samples', 'ControlLayout')
	for control_layout_element in ControlLayout.objects.all():
		control_set, created = ControlSet.objects.get_or_create(layout_name=control_layout_element.layout_name)
		control_layout_element.control_set = control_set
		control_layout_element.save()
		
def control_layout_names_from_reference_layout(apps, schema_editor):
	ControlLayout = apps.get_model('samples', 'ControlLayout')
	for control_layout_element in ControlLayout.objects.all():
		control_layout_element.layout_name = control_layout_element.control_set.layout_name
		control_layout_element.save()
		
def control_sets_for_extraction_batches(apps, schema_editor):
	ControlSet = apps.get_model('samples', 'ControlSet')
	ExtractionBatch = apps.get_model('samples', 'ExtractionBatch')
	for extract_batch in ExtractionBatch.objects.all():
		if len(extract_batch.control_layout_name) > 0:
			extract_batch.control_set = ControlSet.objects.get(layout_name=extract_batch.control_layout_name)
			extract_batch.save()
		
def control_layout_names_from_reference_extraction_batch(apps, schema_editor):
	ExtractionBatch = apps.get_model('samples', 'ExtractionBatch')
	for extract_batch in ExtractionBatch.objects.all():
		if extract_batch.control_set is not None:
			extract_batch.control_layout_name = extract_batch.control_set.layout_name
			extract_batch.save()

def control_sets_for_lysate_batches(apps, schema_editor):
	ControlSet = apps.get_model('samples', 'ControlSet')
	LysateBatch = apps.get_model('samples', 'LysateBatch')
	for lysate_batch in LysateBatch.objects.all():
		if len(lysate_batch.control_layout_name) > 0:
			lysate_batch.control_set = ControlSet.objects.get(layout_name=lysate_batch.control_layout_name)
			lysate_batch.save()

def control_layout_names_from_reference_lysate_batch(apps, schema_editor):
	LysateBatch = apps.get_model('samples', 'LysateBatch')
	for lysate_batch in LysateBatch.objects.all():
		if lysate_batch.control_set is not None:
			lysate_batch.control_layout_name = lysate_batch.control_set.layout_name
			lysate_batch.save()

class Migration(migrations.Migration):

    dependencies = [
        ('samples', '0080_controlset'),
    ]

    operations = [
        migrations.AddField(
            model_name='controllayout',
            name='control_set',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='samples.ControlSet'),
        ),
        migrations.AddField(
            model_name='extractionbatch',
            name='control_set',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='samples.ControlSet'),
        ),
        migrations.AddField(
            model_name='lysatebatch',
            name='control_set',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='samples.ControlSet'),
        ),
		migrations.RunPython(control_sets_from_existing_layouts, control_layout_names_from_reference_layout),
		migrations.RunPython(control_sets_for_extraction_batches, control_layout_names_from_reference_extraction_batch),
		migrations.RunPython(control_sets_for_lysate_batches, control_layout_names_from_reference_lysate_batch),
    ]