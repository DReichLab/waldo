from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from samples.models import CaptureOrShotgunPlate, WetLabStaff

class Command(BaseCommand):
	help = 'Add a single library identified by Reich Lab string to a shotgun or capture plate'
	
	def add_arguments(self, parser):
		parser.add_argument("capture_name")
		parser.add_argument("library_id")
		parser.add_argument('row')
		parser.add_argument('column', type=int)
		parser.add_argument('user', help='Wetlab user first name')
		
	def handle(self, *args, **options):
		with transaction.atomic():
			plate = CaptureOrShotgunPlate.objects.get(name=options['capture_name'])
			library_id = options['library_id']
			row = options['row']
			column = options['column']
			name = options['user']
			wetlab_user = WetLabStaff.objects.get(first_name=name)
			user = wetlab_user.login_user
			
			self.stdout.write(f"{plate.name}\t{library_id}\t{row}\t{column}\t{wetlab_user.name()}")
			plate.add_library(library_id, row, column)
