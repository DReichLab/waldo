from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db import transaction
from samples.models import Library, P5_Index, P7_Index, LibraryBatchLayout, get_wetlab_staff
from samples.management.commands.ess_load import field_check
from samples.layout import plate_location, location_from_indices

class Command(BaseCommand):
	help = 'Load indices for libraries from a file. By default, this will check that populated values match. Missing values are replaced.'
	
	def add_arguments(self, parser):
		parser.add_argument('library_p5_p7', help='File with columns for library id, p5 index, and p7 index')
		parser.add_argument('--override', action='store_true', help='Always replace the values')
		parser.add_argument('-p', '--positions', action='store_true', help='Infer and set well positions')
		parser.add_argument('-u', '--user', required=True)
		
	def handle(self, *args, **options):
		wetlab_user = get_wetlab_staff(options['user'])
		user = wetlab_user.login_user
		
		library_p5_p7 = options['library_p5_p7']
		with open(library_p5_p7) as f:
			with transaction.atomic():
				for line in f:
					fields = line.split()
					library_id = fields[0]
					p5_index = P5_Index.objects.get(sequence=fields[1])
					p7_index = P7_Index.objects.get(sequence=fields[2])

					library = Library.objects.get(reich_lab_library_id=library_id)
					if options['override']:
						library.p5_index = p5_index
						library.p7_index = p7_index
					else:
						field_check(library, 'p5_index', p5_index, True)
						field_check(library, 'p7_index', p7_index, True)
					library.save(save_user=user)
					if options['positions']:
						row, column = plate_location(location_from_indices(p5_index.label, p7_index.label))
						library.librarybatchlayout.row = row
						library.librarybatchlayout.column = column
						library.librarybatchlayout.save(save_user=user)
