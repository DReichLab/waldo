from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from samples.models import LibraryBatch, Library, LIBRARY_POSITIVE, LIBRARY_NEGATIVE, LibraryBatchLayout, P5_Index, P7_Index, WetLabStaff, REICH_LAB, LibraryProtocol

# This should be in create_library_from_extract
def ss(layout_element, i5, i7, user):
	library_batch = layout_element.library_batch
	extract = layout_element.extract
	sample = extract.sample if extract else None

	if layout_element.library is not None:
		return layout_element.library
	else:
		if extract:
			existing_libraries = extract.num_libraries()
			next_library_number = existing_libraries + 1
			reich_lab_library_id = f'{extract.extract_id}.L{next_library_number}'
		elif layout_element.control_type.control_type == LIBRARY_POSITIVE:
			next_library_number = 1 # if there is more than one library positive, we need to check existing
			reich_lab_library_id = f'LP{library_batch.id}.L{next_library_number}'
		# control starting from this step (Mob)
		elif layout_element.control_type.control_type == LIBRARY_NEGATIVE:
			# library negative controls with already created libraries
			num_existing = LibraryBatchLayout.objects.filter(library_batch=library_batch, library__isnull=False, control_type__control_type=LIBRARY_NEGATIVE).count()
			next_library_number = 1
			reich_lab_library_id = f'{control_name_string(library_batch.name, layout_element.control_type, num_existing)}.L{next_library_number}'
		else:
			raise ValueError(f'Unexpected case in creating library, neither extract nor library positive/negative {layout_element.id}')

			raise ValueError(f'single stranded TODO')
	library = Library(sample = sample,
						extract = extract,
						library_batch = library_batch,
						reich_lab_library_id = reich_lab_library_id,
						reich_lab_library_number = next_library_number,
						udg_treatment = 'partial',#library_batch.protocol.udg_treatment,
						library_type = library_batch.protocol.library_type,
						library_prep_lab = REICH_LAB,
						ul_extract_used = library_batch.protocol.volume_extract_used_standard,
						p5_index = i5,
						p7_index = i7
					)
	library.save(save_user=user)
	layout_element.library = library
	layout_element.ul_extract_used = library.ul_extract_used
	layout_element.save(save_user=user)

class Command(BaseCommand):
	help = 'Change '
	
	def add_arguments(self, parser):
		parser.add_argument("library_batch_name")
		parser.add_argument("layout_file")
		parser.add_argument('user', help='Wetlab user first name')
		parser.add_argument('-p', '--protocol', help='library protocol', default='10.1.ssDNA_library_prep_Bravo_v4.0')

	def handle(self, *args, **options):
		library_batch = LibraryBatch.objects.get(name=options['library_batch_name'])

		name = options['user']
		wetlab_user = WetLabStaff.objects.get(first_name=name)
		user = wetlab_user.login_user
		with transaction.atomic():
			library_batch.protocol = LibraryProtocol.objects.get(name=options['protocol'])
			library_batch.technician_fk=wetlab_user
			library_batch.technician=wetlab_user.initials()
			library_batch.save()

			with open(options['layout_file']) as f:
				for line in f:
					well_position_str, i7_str, i5_str = line.split()
					row = well_position_str[0]
					column = int(well_position_str[1:])
					i5 = P5_Index.objects.get(label=i5_str)
					i7 = P7_Index.objects.get(label=i7_str)
					try:
						layout_element = library_batch.layout_elements().get(row=row, column=column)
					except LibraryBatchLayout.DoesNotExist as e:
						self.stderr.write(f'{row} {column}')
						raise e
					ss(layout_element, i5, i7, user)
			library_batch.status = LibraryBatch.CLOSED
			library_batch.save()
