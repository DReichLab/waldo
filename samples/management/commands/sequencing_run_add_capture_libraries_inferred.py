from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from samples.models import CaptureOrShotgunPlate, SequencingRun, CaptureLayout, SequencedLibrary, PCR_NEGATIVE, WetLabStaff

import re

class Command(BaseCommand):
	help = "Add user-specified indexed libraries to a sequencing run from a file input"
	
	def add_arguments(self, parser):
		parser.add_argument('-s', "--sequencing_run", required=True, help='Sequencing run destination')
		parser.add_argument('-u', '--user', required=True, help='Wetlab user first name')
		parser.add_argument('-c', '--create', action='store_true', help='Create sequencing run object')
		parser.add_argument('libraries', help='File with 2 columns: library_id and experiment')
		
	def handle(self, *args, **options):
		with transaction.atomic():
			if options['create']:
				sequencing_run = SequencingRun.objects.create(name=options['sequencing_run'])
			else:
				sequencing_run = SequencingRun.objects.get(name=options['sequencing_run'])
			
			name = options['user']
			wetlab_user = WetLabStaff.objects.get(first_name=name)
			user = wetlab_user.login_user

			with open(options['libraries']) as f:
				header_line = f.readline() # header
				headers = re.split('\t|\n', header_line)
				capture_or_shotgun_batches = []
				for line in f:
					fields = re.split('\t|\n', line)
					library_index = headers.index('library_id')
					library_id = fields[library_index]
					experiment_index = headers.index('experiment')
					experiment = fields[experiment_index]

					if library_id == PCR_NEGATIVE:
						raise NotImplementedError('PCR Negative source without batch is unknown')
					else:
						try:
							layout_element = CaptureLayout.objects.get(library__reich_lab_library_id=library_id, capture_batch__protocol__name=experiment)
						except CaptureLayout.DoesNotExist as e:
							self.stderr.write(f'{library_id}\t{experiment}')
							raise e
						if layout_element.capture_batch not in capture_or_shotgun_batches:
							capture_or_shotgun_batches.append(layout_element.capture_batch)

					# add this indexed library to sequencing run
					try: # if already assigned we can ignore
						sequenced_library = SequencedLibrary.objects.get(indexed_library=layout_element, sequencing_run=sequencing_run)
					except SequencedLibrary.DoesNotExist: # not assigned yet, create assignment
						sequenced_library = SequencedLibrary(indexed_library=layout_element, sequencing_run=sequencing_run)
					sequenced_library.save(save_user=user)
				for batch in capture_or_shotgun_batches:
					assessment = batch.needs_sequencing_assessment()
					self.stdout.write(f'{batch.name}\t{assessment}')
