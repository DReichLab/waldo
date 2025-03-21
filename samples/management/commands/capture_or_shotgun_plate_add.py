from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from samples.models import CaptureOrShotgunPlate, WetLabStaff, get_wetlab_staff, CaptureLayout

class Command(BaseCommand):
	help = 'Add a single library or control identified by Reich Lab string to a shotgun or capture plate'
	
	def add_arguments(self, parser):
		parser.add_argument("capture_name")
		parser.add_argument("library_id", help='Reich lab library indentifier or control string')
		parser.add_argument('row')
		parser.add_argument('column', type=int)
		parser.add_argument('-u', '--user', nargs='+', required=True, help='Wetlab Staff name or username')
		parser.add_argument('-d', '--delete', action='store_true', help='Remove this library from position instead of adding')
		
	def handle(self, *args, **options):
		with transaction.atomic():
			plate = CaptureOrShotgunPlate.objects.get(name=options['capture_name'])
			library_id = options['library_id']
			row = options['row']
			column = options['column']
			wetlab_user = get_wetlab_staff(options['user'])
			user = wetlab_user.login_user
			
			if not options['delete']:
				self.stdout.write(f"{plate.name}\t{library_id}\t{row}\t{column}\t{wetlab_user.name()}")
				plate.add_library(library_id, row, column, user)
			else:
				element = CaptureLayout.objects.get(row=row, column=column, library__reich_lab_library_id=library_id, capture_batch=plate)
				element.delete()
