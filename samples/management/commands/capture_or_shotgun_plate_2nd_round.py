from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from samples.models import CaptureOrShotgunPlate, WetLabStaff, CaptureLayout

import re

class Command(BaseCommand):
	help = 'Reuse indices from an existing capture for a new capture for a list of captured libraries'
	
	def add_arguments(self, parser):
		parser.add_argument("--capture_name", required=True, help='Capture/shotgun batch to be filled')
		parser.add_argument("--prior_captures", required=True, nargs='+', help='Prior capture/shotgun batches that will have indices reused')
		parser.add_argument('--user', required=True, help='Wetlab user first name')
		parser.add_argument('library_positions', help='File with two tab-delimited columns: library_id and position')
		
	def handle(self, *args, **options):
		with transaction.atomic():
			plate = CaptureOrShotgunPlate.objects.get(name=options['capture_name'])
			name = options['user']
			wetlab_user = WetLabStaff.objects.get(first_name=name)
			user = wetlab_user.login_user

			with open(options['library_positions']) as f:
				f.readline() # discard header
				for line in f:
					fields = re.split('\t|\n', line)
					library_id = fields[0]
					position = fields[1]
					row = position[0]
					column = int(position[1:])

					self.stdout.write(f"{plate.name}\t{library_id}\t{row}\t{column}\t{wetlab_user.name()}")
					layout_element = plate.add_library(library_id, row, column, user)
					# use indices from prior runs
					if layout_element.library is not None:
						prior_element = CaptureLayout.objects.get(capture_batch__name__in=options['prior_captures'], library__reich_lab_library_id=library_id)
					else:
						prior_element = CaptureLayout.objects.get(capture_batch__name__in=options['prior_captures'], control_type=prior_element.control_type)

					layout_element.p5_index = prior_element.p5_index
					layout_element.p7_index = prior_element.p7_index
					layout_element.save(save_user=user)
