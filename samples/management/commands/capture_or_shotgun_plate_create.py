from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from samples.models import LibraryBatch, CaptureOrShotgunPlate, WetLabStaff

class Command(BaseCommand):
	help = 'Create a capture or shotgun plate allowing exact selection'
	
	def add_arguments(self, parser):
		parser.add_argument("capture_name")
		parser.add_argument('library_batches', nargs='+')
		parser.add_argument('--user', help='Wetlab user first name')
		
	def handle(self, *args, **options):
		with transaction.atomic():
			name = options['user']
			wetlab_user = WetLabStaff.objects.get(first_name=name)
			user = wetlab_user.login_user

			first_library_batch_str = options['library_batches'][0]
			other_names = options['library_batches'][1:]
			
			first_library_batch = LibraryBatch.objects.get(name=first_library_batch_str)
			other_library_batches = LibraryBatch.objects.filter(name__in=other_names)

			first_library_batch.create_capture(options['capture_name'], other_library_batches, user)
