# Generated by Django 3.0.3 on 2023-04-10 14:02

from django.db import migrations, models

def i5_defaults(apps, queryset):
	P5_Index = apps.get_model('samples', 'P5_Index')
	for index in P5_Index.objects.all():
		label = index.label
		if label.endswith('ss'):
			label = label[:-2]
		try:
			any_integer = int(label)
			index.reich_lab_default = True
			index.save()
		except ValueError:
			pass


def i7_defaults(apps, queryset):
	P7_Index = apps.get_model('samples', 'P7_Index')
	for index in P7_Index.objects.all():
		label = index.label
		try:
			any_integer = int(label)
			index.reich_lab_default = True
			index.save()
		except ValueError:
			pass

def barcode_defaults(apps, queryset):
	Barcode = apps.get_model('samples', 'Barcode')
	for barcode in Barcode.objects.all():
		label = barcode.label
		if label.startswith('Q'):
			barcode.reich_lab_default = True
			barcode.save()

def do_nothing(apps, queryset):
    pass

class Migration(migrations.Migration):

	dependencies = [
		('samples', '0174_sequenced_library_new_fields'),
	]

	operations = [
		migrations.AddField(
			model_name='barcode',
			name='reich_lab_default',
			field=models.BooleanField(default=False),
		),
		migrations.AddField(
			model_name='p5_index',
			name='reich_lab_default',
			field=models.BooleanField(default=False),
		),
		migrations.AddField(
			model_name='p7_index',
			name='reich_lab_default',
			field=models.BooleanField(default=False),
		),
		migrations.RunPython(i5_defaults, do_nothing),
		migrations.RunPython(i7_defaults, do_nothing),
		migrations.RunPython(barcode_defaults, do_nothing),
	]
