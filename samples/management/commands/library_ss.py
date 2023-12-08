from django.core.management.base import BaseCommand, CommandError
from django.core.files import File
from django.db import transaction
from samples.models import ExtractionBatch, LibraryBatch, LIBRARY_POSITIVE, LIBRARY_NEGATIVE, LibraryBatchLayout, P5_Index, P7_Index, WetLabStaff, REICH_LAB, LibraryProtocol, create_library_from_extract, Extract, ControlSet

class Command(BaseCommand):
	help = 'Populate a library batch with libraries from existing extracts.'
	
	def add_arguments(self, parser):
		parser.add_argument("library_batch_name")
		parser.add_argument("layout_file")
		parser.add_argument('user', help='Wetlab user first name')
		parser.add_argument('-p', '--protocol', help='library protocol', default='10.1.ssDNA_library_prep_Bravo_v4.2')
		parser.add_argument('-s', '--source_extract_batch', help='Create new library batch from this extract batch.')
		parser.add_argument('-n', '--new_batch', action='store_true', help='Create new library batch')
		parser.add_argument('-c', '--controls', default='DS_2_2_1', help='control layout to use')
		parser.add_argument('-e', '--extract_ul', help='Use this many ul of extract for each library.', type=float)

	def handle(self, *args, **options):
		name = options['user']
		wetlab_user = WetLabStaff.objects.get(first_name=name)
		user = wetlab_user.login_user

		with transaction.atomic():
			if options['source_extract_batch']:
				extract_batch = ExtractionBatch.objects.get(batch_name=options['source_extract_batch'])
				library_batch = extract_batch.create_library_batch(options['library_batch_name'], user)
			elif options['new_batch']:
				library_batch, created = LibraryBatch.objects.get_or_create(name=options['library_batch_name'])
				library_batch.control_set = ControlSet.objects.get(layout_name=options['controls'])
				library_batch.set_controls(user)
			else:
				library_batch = LibraryBatch.objects.get(name=options['library_batch_name'])

			library_batch.protocol = LibraryProtocol.objects.get(name=options['protocol'])
			library_batch.technician_fk=wetlab_user
			library_batch.technician=wetlab_user.initials()
			library_batch.save()

			if options['extract_ul']:
				ul_extract_used = options['extract_ul']
			else:
				ul_extract_used = library_batch.protocol.volume_extract_used_standard

			with open(options['layout_file']) as f:
				single_stranded_file = File(f)
				library_batch.single_stranded_from_file(single_stranded_file, user, ul_extract_used=ul_extract_used)
