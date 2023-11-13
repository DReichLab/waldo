from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from samples.models import LibraryBatch, LibraryBatchLayout

class Command(BaseCommand):
	help = "Rotate a library batch. Optionally delete libraries to get barcodes to match wells."
	
	def add_arguments(self, parser):
		parser.add_argument('library_batch')
		parser.add_argument('-d', '--delete_libraries', action='store_true')
		
	def handle(self, *args, **options):
		library_batch = LibraryBatch.objects.get(name=options['library_batch'])
		library_batch.rotated = not library_batch.rotated
		library_batch.save()

		for layout_element in library_batch.layout_elements():
			layout_element.rotate()
			if options['delete_libraries']:
				library = layout_element.library
				if library is not None:
					library.delete()
				layout_element.library = None
			layout_element.save()
