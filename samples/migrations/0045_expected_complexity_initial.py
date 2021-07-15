# Generated by Django 3.0.4 on 2021-07-15 20:26

from django.db import migrations

# add expected complexity categories
def add_initial_powder_batch_status(apps, schema_editor):
	ExpectedComplexity = apps.get_model('samples', 'ExpectedComplexity')
	ExpectedComplexity.objects.get_or_create(description='low', sort_order=0)
	ExpectedComplexity.objects.get_or_create(description='high', sort_order=100)

def values_will_not_be_reversed(apps, schema_editor):
	pass

class Migration(migrations.Migration):

    dependencies = [
        ('samples', '0044_expectedcomplexity_sampleprepqueue'),
    ]

    operations = [
		migrations.RunPython(add_initial_powder_batch_status, values_will_not_be_reversed),
    ]
