# Generated by Django 3.0.4 on 2022-08-10 18:08

from django.db import migrations

def remove_fake_lysates(apps, queryset):
	Lysate = apps.get_model('samples', 'Lysate')
	Extract = apps.get_model('samples', 'Extract')
	LysateBatchLayout = apps.get_model('samples', 'LysateBatchLayout')
	ExtractionBatchLayout = apps.get_model('samples', 'ExtractionBatchLayout')
	
	for lysate in Lysate.objects.filter(lysate_id__endswith='.NY'):
		for extract in Extract.objects.filter(lysate=lysate):
			extract.sample = lysate.powder_sample.sample
			extract.lysate = None
			extract.save()
		for lysate_layout_element in LysateBatchLayout.objects.filter(lysate=lysate):
			lysate_layout_element.delete()
		for extract_layout_element in ExtractionBatchLayout.objects.filter(lysate=lysate):
			extract_layout_element.lysate = None
			extract_layout_element.save()
		lysate.delete()


class Migration(migrations.Migration):

	dependencies = [
		('samples', '0166_remove_fake_extracts'),
	]

	operations = [
		migrations.RunPython(remove_fake_lysates),
	]
