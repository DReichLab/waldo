# Generated by Django 3.0.4 on 2021-05-12 17:13

from django.db import migrations

# add initial categories
def add_initial_powder_batch_status(apps, schema_editor):
	PowderBatchStatus = apps.get_model('samples', 'PowderBatchStatus')
	PowderBatchStatus.objects.get_or_create(description='Open', sort_order=0)
	PowderBatchStatus.objects.get_or_create(description='Closed', sort_order=100)
	PowderBatchStatus.objects.get_or_create(description='Ready For Plate', sort_order=200)
	
def values_will_not_be_reversed(apps, schema_editor):
	pass

class Migration(migrations.Migration):

    dependencies = [
        ('samples', '0038_auto_20210512_1313'),
    ]

    operations = [
		migrations.RunPython(add_initial_powder_batch_status, values_will_not_be_reversed),
    ]
