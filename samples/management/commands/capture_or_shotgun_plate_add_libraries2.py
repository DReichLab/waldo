from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from samples.models import CaptureOrShotgunPlate, WetLabStaff, CaptureLayout, CAPTURE_POSITIVE, CAPTURE_POSITIVE_LIBRARY_NAME_DS, P5_Index, P7_Index, get_value

import re

class Command(BaseCommand):
	help = 'Add libraries identified by Reich Lab string to a shotgun or capture plate. This is tweaked for Kawaka to reuse indices without having to specify prior batches.'
	
	def add_arguments(self, parser):
		parser.add_argument("--capture_name", required=True)
		parser.add_argument('--user', help='Wetlab user first name')
		parser.add_argument('library_positions', help='File with two columns: library_id and position')
		parser.add_argument("--create", action='store_true', help='Create a new capture/shotgun batch')
		parser.add_argument("--i5", help='capture positive i5')
		parser.add_argument("--i7", help='capture positive i7')
		
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

					try:
						p5_index = None
						p7_index = None
						# all capture positives are currently double-stranded
						if library_id == CAPTURE_POSITIVE or library_id == CAPTURE_POSITIVE_LIBRARY_NAME_DS:
							if options['i5']:
								p5_index = P5_Index.objects.get(label=options['i5'])
							if options['i7']:
								p7_index = P7_Index.objects.get(label=options['i7'])
						else:
							existing_layouts = CaptureLayout.objects.filter(library__reich_lab_library_id=library_id)
							for existing_layout in existing_layouts:
								p5_label = get_value(existing_layout, 'p5_index', 'label')
								p7_label = get_value(existing_layout, 'p7_index', 'label')
								self.stdout.write(f'{library_id} {p5_label} {p7_label}')

								if p5_index is not None:
									if p5_index != existing_layout.p5_index:
										raise ValueError(f'Expecting only one prior index {library_id} {p5_index.label} {CAPTURE_POSITIVE} {existing_layout.p5_index.label}')
								else:
									p5_index = existing_layout.p5_index
								if p7_index is not None:
									if p7_index != existing_layout.p7_index:
										raise ValueError(f'Expecting only one prior index {library_id} {p7_index.label} {existing_layout.p7_index.label}')
								else:
									p7_index = existing_layout.p7_index

					except CaptureLayout.DoesNotExist:
						existing_layout = None

					self.stdout.write(f"{plate.name}\t{library_id}\t{row}\t{column}\t{wetlab_user.name()}")
					layout_element = plate.add_library(library_id, row, column, user)
					if p5_index and p7_index:
						layout_element.p5_index = p5_index
						layout_element.p7_index = p7_index
						layout_element.save(save_user=user)
