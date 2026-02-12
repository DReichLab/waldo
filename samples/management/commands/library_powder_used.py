from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from samples.models import Library

class Command(BaseCommand):
	help = 'For a list of libraries, output powder used equivalent and total amount of powder used in creating corresponding extract or lysate'
	
	def add_arguments(self, parser):
		parser.add_argument("libraries", nargs='*')
		parser.add_argument("-f", '--libraries_file', help='file containing list of libraries')
		
	def handle(self, *args, **options):
		if options['libraries_file']:
			with open(options['libraries_file']) as f:
				libraries = [line.strip() for line in f]
		else:
			libraries = []

		for library_str in libraries + options['libraries']:
			library = Library.objects.get(reich_lab_library_id=library_str)
			powder_equivalent = library.powder_equivalent()
			total_extraction_powder = library.extract.total_extraction_powder()
			self.stdout.write('\t'.join([library_str, f'{powder_equivalent:.2f}', f'{total_extraction_powder:.1f}']))
