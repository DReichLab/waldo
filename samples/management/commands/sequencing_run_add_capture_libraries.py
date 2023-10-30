from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from samples.models import CaptureOrShotgunPlate, SequencingRun, CaptureLayout, SequencedLibrary, PCR_NEGATIVE, WetLabStaff

import re

class Command(BaseCommand):
	help = "Add user-specified indexed libraries to a sequencing run from a file input"
	
	def add_arguments(self, parser):
		parser.add_argument("--capture_name", required=True, help='Source for indexed libraries to add to sequencing run')
		parser.add_argument("--sequencing_run", required=True, help='Sequencing run destination')
		parser.add_argument('--user', required=True, help='Wetlab user first name')
		parser.add_argument('--create', action='store_true', help='Create sequencing run object')
		parser.add_argument('library_positions', help='File with two columns: library_id and position')
		parser.add_argument('-i', '--ignore_positions', help='Load libraries from capture based on library id only. If library is not unique, command will fail.', action='store_true')
		
	def handle(self, *args, **options):
		with transaction.atomic():
			capture = CaptureOrShotgunPlate.objects.get(name=options['capture_name'])

			if options['create']:
				sequencing_run = SequencingRun.objects.create(name=options['sequencing_run'])
			else:
				sequencing_run = SequencingRun.objects.get(name=options['sequencing_run'])
			
			name = options['user']
			wetlab_user = WetLabStaff.objects.get(first_name=name)
			user = wetlab_user.login_user

			with open(options['library_positions']) as f:
				f.readline() # discard header
				for line in f:
					fields = re.split('\t|\n', line)
					library_id = fields[0]

					if options['ignore_positions']:
						if library_id == PCR_NEGATIVE:
							layout_element = CaptureLayout.objects.get(capture_batch=capture, control_type__control_type=PCR_NEGATIVE)
						else:
							layout_element = CaptureLayout.objects.get(capture_batch=capture, library__reich_lab_library_id=library_id)
					else:
						position = fields[1]
						row = position[0]
						column = int(position[1:])
						if library_id == PCR_NEGATIVE:
							layout_element = CaptureLayout.objects.get(capture_batch=capture, row=row, column=column, control_type__control_type=PCR_NEGATIVE)
						else:
							layout_element = CaptureLayout.objects.get(capture_batch=capture, row=row, column=column, library__reich_lab_library_id=library_id)
					# add this indexed library to sequencing run
					sequenced_library = SequencedLibrary(indexed_library=layout_element, sequencing_run=sequencing_run)
					sequenced_library.save(save_user=user)
