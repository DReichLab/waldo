from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db import transaction

import re

from samples.models import LibraryBatch, Extract

class Command(BaseCommand):
	help = "Add extract to a library batch well for each line in file"
	
	def add_arguments(self, parser):
		parser.add_argument('library_batch')
		parser.add_argument('-f', '--extracts_file', help='File containing two columns: position (B8) and extract id string', required=True)
		
	def handle(self, *args, **options):
		library_batch = LibraryBatch.objects.get(name=options['library_batch'])
		with transaction.atomic():
			with open(options['extracts_file']) as f:
				for line in f:
					fields = line.split()
					position = fields[0]
					row = position[0]
					column = int(position[1:])
					extract_id = fields[1]

					extract = Extract.objects.get(extract_id=extract_id)

					self.stdout.write(extract.extract_id)
					library_batch.assign_extract(extract, row, column)
			library_batch.clean()
