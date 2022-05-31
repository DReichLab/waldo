from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from samples.models import ExtractionBatch, Library, Lysate

class Command(BaseCommand):
	help = 'Add a single lysate identified by Reich Lab a reich lab library id to a shotgun or capture plate'
	
	def add_arguments(self, parser):
		parser.add_argument("extract_batch_name")
		parser.add_argument('parameter_file')
		
	def handle(self, *args, **options):
		plate = ExtractionBatch.objects.get(batch_name=options['extract_batch_name'])
		with open(options['parameter_file']) as f:
			for line in f:
				fields = line.split()
				library_id = fields[0]
				plate_location = fields[1]
				
				self.stdout.write(f"{plate.batch_name}\t{library_id}\t{plate_location}")
				
				#with transaction.atomic():
				if library_id.startswith('S'):
					row = plate_location[0]
					column = int(plate_location[1:])
					
					library = Library.objects.get(reich_lab_library_id=library_id)
					lysate = library.extract.lysate
					plate.add_lysate(lysate, row, column)
			#plate.add_library(library_id, row, column)
