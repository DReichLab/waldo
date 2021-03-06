# Generated by Django 3.0.4 on 2022-07-22 20:58

from django.db import migrations

OLD_STOP_VALUE = -100
NEW_STOP_VALUE = 1000

def change_stop_value(apps, value_to_change, new_value):
	PowderBatch = apps.get_model('samples', 'PowderBatch')
	
	for powder_batch in PowderBatch.objects.filter(status=value_to_change):
		powder_batch.status = new_value
		powder_batch.save()

def new_powder_batch_stop_value(apps, queryset):
	change_stop_value(apps, OLD_STOP_VALUE, NEW_STOP_VALUE)
   
def old_powder_batch_stop_value(apps, queryset):
	change_stop_value(apps, NEW_STOP_VALUE, OLD_STOP_VALUE)

class Migration(migrations.Migration):

	dependencies = [
		('samples', '0160_radiocardon_dated_sample_additions'),
	]

	operations = [
		migrations.RunPython(new_powder_batch_stop_value, old_powder_batch_stop_value),
	]
