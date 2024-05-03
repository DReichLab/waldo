from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db import transaction

from samples.models import LibraryBatch, LibraryBatchLayout, get_value, Extract

class Command(BaseCommand):
	help = "Remove the extract assigned to a well and the associated library"
	
	def add_arguments(self, parser):
		parser.add_argument('library_batch')
		parser.add_argument('row')
		parser.add_argument('column', type=int)
		parser.add_argument('extract_id')
		
	def handle(self, *args, **options):
		with transaction.atomic():
			library_batch = LibraryBatch.objects.get(name=options['library_batch'])
			extract = Extract.objects.get(extract_id=options['extract_id'])
			row = options['row']
			column = options['column']

			self.stdout.write(extract.extract_id)
			library_batch.assign_extract(extract, row, column)
