# Generated by Django 3.0.4 on 2022-04-07 21:29

from django.db import migrations

def fill_powder_batch_for_lysate_batch_layout(apps, queryset):
	LysateBatchLayout = apps.get_model('samples', 'LysateBatchLayout')
	PowderSample = apps.get_model('samples', 'PowderSample')

	for layout_element in LysateBatchLayout.objects.all():
		powder_sample = layout_element.powder_sample
		# Does this powder sample show up in more than one LysateBatch?
		powder_sample_appearances = LysateBatchLayout.objects.filter(powder_sample=powder_sample).count()
		if powder_sample is not None:
			if powder_sample_appearances == 1:
				layout_element.powder_batch = powder_sample.powder_batch
				layout_element.save()
			elif powder_sample_appearances == 0:
				pass
			else:
				powder_sample_str = powder_sample.powder_sample_id if powder_sample else 'N/A'
				batch_name = layout_element.lysate_batch.batch_name if layout_element.lysate_batch else ''
				print(f'LysateBatchLayout {layout_element.id} powder sample {powder_sample_str} lysate batch {batch_name} {powder_sample_appearances}')

    
def do_nothing(apps, queryset):
	pass

class Migration(migrations.Migration):
	dependencies = [
		('samples', '0151_lysatebatchlayout_powder_batch'),
	]

	operations = [
		migrations.RunPython(fill_powder_batch_for_lysate_batch_layout, do_nothing),
	]