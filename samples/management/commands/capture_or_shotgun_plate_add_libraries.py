from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from samples.models import CaptureOrShotgunPlate, WetLabStaff, get_wetlab_staff

import re

class Command(BaseCommand):
	help = 'Add libraries identified by Reich Lab string to a shotgun or capture plate'
	
	def add_arguments(self, parser):
		parser.add_argument("--capture_name", required=True)
		parser.add_argument('-u', '--user', nargs='+', required=True, help='Wetlab Staff name or username')
		parser.add_argument('library_positions', help='File with two columns: library_id and position')
		parser.add_argument("--create", action='store_true', help='Create a new capture/shotgun batch')
		parser.add_argument('-n', '--no_position', action='store_true')
		parser.add_argument('--non_control', action='store_true', help='For external libraries without LibraryBatchLayout objects, this indicates non-control libraries')
		
	def handle(self, *args, **options):
		with transaction.atomic():
			wetlab_user = get_wetlab_staff(options['user'])
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
					if options['no_position']:
						row = None
						column = None
					else:
						position = fields[1]
						row = position[0]
						column = int(position[1:])

					self.stdout.write(f"{plate.name}\t{library_id}\t{row}\t{column}\t{wetlab_user.name()}")
					plate.add_library(library_id, row, column, user, non_control_library=options['non_control'])
