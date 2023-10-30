from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from samples.models import CaptureOrShotgunPlate, WetLabStaff

import re

class Command(BaseCommand):
	help = 'Add libraries identified by Reich Lab string to a shotgun or capture plate'
	
	def add_arguments(self, parser):
		parser.add_argument("--capture_name", required=True)
		parser.add_argument('--user', help='Wetlab user first name')
		parser.add_argument('library_positions', help='File with two columns: library_id and position')
		parser.add_argument("--create", action='store_true', help='Create a new capture/shotgun batch')
		
	def handle(self, *args, **options):
		with transaction.atomic():
			name = options['user']
			wetlab_user = WetLabStaff.objects.get(first_name=name)
			user = wetlab_user.login_user

			if options['create']:
				plate = CaptureOrShotgunPlate(name=options['capture_name'])
				plate.save(save_user=user)
			else:
				plate = CaptureOrShotgunPlate.objects.get(name=options['capture_name'])

			with open(options['library_positions']) as f:
				f.readline() # discard header
				for line in f:
					fields = re.split('\t|\n', line)
					library_id = fields[0]
					position = fields[1]
					row = position[0]
					column = int(position[1:])

					self.stdout.write(f"{plate.name}\t{library_id}\t{row}\t{column}\t{wetlab_user.name()}")
					plate.add_library(library_id, row, column, user)
