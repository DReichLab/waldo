from django.core.management.base import BaseCommand
from django.db import transaction
from samples.models import LibraryBatch
from django.contrib.auth.models import User

class Command(BaseCommand):
	help = 'Change UDG treatment for a library batch'
	
	def add_arguments(self, parser):
		parser.add_argument('-n', '--library_batch_name', required=True)
		parser.add_argument('--udg', required=True)
		parser.add_argument('--user', help='login user')
		
	def handle(self, *args, **options):
		library_batch_name = options['library_batch_name']
		udg = options['udg']

		user = None
		if options['user']:
			name = options['user']
			user = User.objects.get(username=name)

		library_batch = LibraryBatch.objects.get(name=library_batch_name)
		with transaction.atomic():
			for layout_element in library_batch.layout_elements():
				library = layout_element.library
				if library:
					library.udg_treatment = udg
					library.save(save_user=user)
