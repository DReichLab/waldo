from django.core.management.base import BaseCommand, CommandError
from samples.models import ExtractionBatch, Library, WetLabStaff

import re

class Command(BaseCommand):
	help = 'Add lysates identified by Reich Lab library id to a shotgun or capture plate. This plate must already exist.'
	
	def add_arguments(self, parser):
		parser.add_argument('--controls', action='store_true', help="Populate lysate batch's control layout")
		parser.add_argument('user')
		parser.add_argument("extract_batch_name")
		parser.add_argument('parameter_file')
		
	def handle(self, *args, **options):
		plate = ExtractionBatch.objects.get(batch_name=options['extract_batch_name'])
		
		# This needs enhancement if there are duplicate names
		name = options['user']
		wetlab_user = WetLabStaff.objects.get(first_name=name)
		user = wetlab_user.login_user
		
		if options['controls']:
			plate.set_controls(user)
		
		# This file contains library id and position, one per line
		with open(options['parameter_file']) as f:
			for line in f:
				fields = re.split('\t', line)
				library_id = fields[0].strip()
				plate_location = fields[1].strip()
				
				self.stdout.write(f"{plate.batch_name}\t{library_id}\t{plate_location}")
				
				#with transaction.atomic():
				if library_id.startswith('S'):
					row = plate_location[0]
					column = int(plate_location[1:])
					
					library = Library.objects.get(reich_lab_library_id=library_id)
					lysate = library.extract.lysate
					plate.add_lysate(lysate, row, column, user)
				else:
					self.stderr.write(f'skipping {library_id}')
