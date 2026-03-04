from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from samples.models import CaptureOrShotgunPlate, WetLabStaff, get_wetlab_staff, P5_Index, P7_Index
from samples.management.commands.ess_load import field_check

import re

class Command(BaseCommand):
	help = 'Add libraries identified by Reich Lab string to a shotgun or capture plate. Optionally add indices. Barcodes need to be present to add indices for double-stranded libraries.'
	
	def add_arguments(self, parser):
		parser.add_argument("--capture_name", required=True)
		parser.add_argument('-u', '--user', nargs='+', required=True, help='Wetlab Staff name or username')
		parser.add_argument('library_positions', help='File with two columns: library_id and position')
		parser.add_argument("--create", action='store_true', help='Create a new capture/shotgun batch')
		parser.add_argument('-n', '--no_position', action='store_true')
		parser.add_argument('--non_control', action='store_true', help='For external libraries without LibraryBatchLayout objects, this indicates non-control libraries')
		parser.add_argument('--indices', action='store_true', help='Add indices to layout elements of libraries with barcodes (ds), and to library if no barcodes are present (ss). i5 sequence in column 3, i7 sequence in column 4.')
		
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
					library_id = fields[0].strip()
					if options['no_position']:
						row = None
						column = None
					else:
						position = fields[1].strip()
						row = position[0]
						column = int(position[1:])

					self.stdout.write(f"{plate.name}\t{library_id}\t{row}\t{column}\t{wetlab_user.name()}")
					layout_element = plate.add_library(library_id, row, column, user, non_control_library=options['non_control'])
					if options['indices']:
						i5 = P5_Index.objects.get(sequence=fields[2].strip())
						i7 = P7_Index.objects.get(sequence=fields[3].strip())
						if layout_element.library.p5_barcode and layout_element.library.p7_barcode:
							field_check(layout_element, 'p5_index', i5, True)
							field_check(layout_element, 'p7_index', i7, True)
							layout_element.save(save_user=user)
						else:
							library = layout_element.library
							field_check(library, 'p5_index', i5, True)
							field_check(library, 'p7_index', i7, True)
							library.save(save_user=user)
