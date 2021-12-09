from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db import transaction

import argparse, sys

from samples.models import Sample, LibraryBatch, Extract, TimestampedWellPosition, CONTROL_CHARACTERS, ControlType, LIBRARY_NEGATIVE, LIBRARY_POSITIVE, REICH_LAB, LibraryBatchLayout

class Command(BaseCommand):
	help = "Assign extracts to a library batch from a file input with well positions for extracts, library negatives, library positive, and external samples arriving as extracts."
	
	def add_arguments(self, parser):
		parser.add_argument('library_batch_name')
		parser.add_argument('extract_layouts', type=argparse.FileType('r'), help="position and extract ids")
		
	def handle(self, *args, **options):
		library_batch = LibraryBatch.objects.get(name=options['library_batch_name'])
		control_sample_number = None
		library_negative_control_count = 0
		library_negative_control_type = ControlType.objects.get(control_type=LIBRARY_NEGATIVE)
		
		with transaction.atomic():
			with options['extract_layouts'] as extract_layouts:
				for line in extract_layouts:
					fields = [x.strip() for x in line.split('\t')]
					well_position = fields[0]
					id_to_parse = fields[1]
					
					position = TimestampedWellPosition()
					position.set_position(well_position)
					
					# existing extracts
					if id_to_parse.startswith('S'):
						extract_id = id_to_parse
						extract = Extract.objects.get(extract_id=extract_id)
						
						library_batch.assign_extract(extract, position.row, position.column)
					elif id_to_parse == LIBRARY_NEGATIVE:
						control_character = CONTROL_CHARACTERS[library_negative_control_count]
						library_negative_control_count += 1
						control_sample = Sample(control=control_character)
						if control_sample_number is not None:
							control_sample.reich_lab_id = control_sample_number
							control_sample.save()
						else:
							control_sample_number = control_sample.assign_reich_lab_sample_number()
							
						extract = control_sample.originating_extract(REICH_LAB)
						library_batch.assign_extract(extract, position.row, position.column, library_negative_control_type)
					elif id_to_parse == 'Contl.Positive':
						LibraryBatchLayout.objects.create(library_batch=library_batch, extract=None, control_type=ControlType.objects.get(control_type=LIBRARY_POSITIVE), row=position.row, column=position.column)
					else: # external sample arriving as an extract, need to create extract entry
						raw_sample_id = id_to_parse # non-Reich lab sample number (primary key)
						sample = Sample.objects.get(id=raw_sample_id)
						extract = sample.originating_extract('Pinhasi Lab') # TODO this should be an argument
						library_batch.assign_extract(extract, position.row, position.column)
