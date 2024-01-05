from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db import transaction

from samples.models import LibraryBatch, LibraryBatchLayout, get_value

class Command(BaseCommand):
	help = "Remove the extract assigned to a well and the associated library"
	
	def add_arguments(self, parser):
		parser.add_argument('library_batch')
		parser.add_argument('row')
		parser.add_argument('column', type=int)
		parser.add_argument('-d', '--delete', action='store_true')
		
	def handle(self, *args, **options):
		with transaction.atomic():
			library_batch = LibraryBatch.objects.get(name=options['library_batch'])
			layout_element = LibraryBatchLayout.objects.get(library_batch=library_batch, row=options['row'], column=options['column'])
			extract_id = get_value(layout_element, 'extract', 'extract_id')
			self.stdout.write(f'{extract_id}')
			if layout_element.library:
				library_id = get_value(layout_element, 'library', 'reich_lab_library_id')
				self.stdout.write(f'{library_id}')
			if options['delete']:
				layout_element.delete()
