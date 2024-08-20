from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db import transaction
from samples.models import P5_Index, P7_Index

class Command(BaseCommand):
	help = 'import indices from file'
	
	def add_arguments(self, parser):
		parser.add_argument("type", choices=['i5', 'i7'])
		parser.add_argument("barcodes_file")
		parser.add_argument('-d', "--default",  action='store_true')
		
	def handle(self, *args, **options):
		barcode_type = options['type']
		barcodes_file = options['barcodes_file']
		default = options['default']
		
		if barcode_type == 'i5':
			barcodes = P5_Index.objects
		elif barcode_type == 'i7':
			barcodes = P7_Index.objects

		with transaction.atomic():
			with open(barcodes_file) as f:
				for line in f:
					fields = line.split()
					label = fields[0]
					sequence = fields[1]
					barcode, created = barcodes.get_or_create(label=label, sequence=sequence, reich_lab_default=default)
					barcode.full_clean()
