# Generated by Django 3.0.4 on 2021-02-08 22:54

from django.db import migrations
from sequencing_run.library_id import LibraryID

import re
import sys

# fill in lysate number from string
def lysate_number(apps, schema_editor):
	Lysate = apps.get_model('samples', 'Lysate')
	
	for lysate in Lysate.objects.all():
		lysate_string = lysate.lysate_id
		m = re.match('S(\d+)([a-zA-Z]*)\.Y(\d+)', lysate_string)
		if m is not None:
			lysate.reich_lab_lysate_number = int(m.group(3))
			lysate.save()
			
'''
These are valid extract ids for the migration:
S12772.Y1.E1
S25361.E1
S7578.NY.E1 (not a valid library id beginning)
S20592.EL1.E1 (not a valid library id beginning)
'''
def extract_number(apps, schema_editor):
	Extract = apps.get_model('samples', 'Extract')
	Sample = apps.get_model('samples', 'Sample')
	errors = []
	for extract in Extract.objects.all():
		extract_string = extract.extract_id
		m = re.match('S(\d+)([a-zA-Z]*)\.', extract_string)
		sample_number = int(m.group(1))
		control = m.group(2)
		extract_string_minus_sample = extract_string[m.end():]
		
		m2 = re.match('(((NY)|(EL(\d+))|(Y(\d+)))\.)?', extract_string_minus_sample)
		extract_only_string = extract_string_minus_sample[m2.end():]
		
		m3 = re.match('E(?P<extract>\d+)', extract_only_string)
		if m3 is None:
			extract.reich_lab_extract_number = None
		else:
			extract.reich_lab_extract_number = int(m3.group('extract'))
		
		extract.sample = Sample.objects.get(reich_lab_id = sample_number, control = control)
		# sample number consistency
		if sample_number != extract.lysate_id.powder_sample.sample.reich_lab_id:
			errors.append(f'{extract_string} extract: sample mismatch {extract.lysate_id.powder_sample.sample.reich_lab_id}')
		extract.save()
	if len(errors) > 0:
		raise ValueError('\n'.join(errors))
		
	
def library_number(apps, schema_editor):
	Library = apps.get_model('samples', 'Library')
	Sample = apps.get_model('samples', 'Sample')
	for library in Library.objects.all():
		reich_lab_library_id = library.reich_lab_library_id
		library_id = LibraryID(reich_lab_library_id)
		library.reich_lab_library_number = library_id.library
		
		if library_id.sample_suffix is None:
			try:
				library.sample = Sample.objects.get(reich_lab_id = library_id.sample, control=library_id.sample_suffix)
			except Sample.DoesNotExist as e:
				print(library_id, file=sys.stderr)
				raise e
			# verify sample consistency
			if library_id.sample != library.extract_id.lysate_id.powder_sample.sample.reich_lab_id:
				raise ValueError(f'{reich_lab_library_id} library: sample mismatch')
			
			# extract consistency
			if library_id.extract != library.extract_id.reich_lab_extract_number:
				raise ValueError(f'{reich_lab_library_id} library: extract mismatch')
		else:
			library.sample = None
		
		library.save()

class Migration(migrations.Migration):

    dependencies = [
        ('samples', '0024_auto_20210208_1729'),
    ]

    operations = [
		migrations.RunPython(lysate_number, None),
		migrations.RunPython(extract_number, None),
		migrations.RunPython(library_number, None),
    ]