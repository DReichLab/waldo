from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from samples.models import P5_Index, P7_Index

class Command(BaseCommand):
	help = 'import indices from file'
	
	def add_arguments(self, parser):
		parser.add_argument("type", choices=['i5', 'i7'])
		parser.add_argument("barcodes_file")
		
	def handle(self, *args, **options):
		barcode_type = options['type']
		barcodes_file = options['barcodes_file']
		
		if barcode_type == 'i5':
			barcodes = P5_Index.objects
		elif barcode_type == 'i7':
			barcodes = P7_Index.objects

		with open(barcodes_file) as f:
			for line in f:
				fields = line.split()
				label = fields[0]
				sequence = fields[1]
				barcodes.get_or_create(label=label, sequence=sequence)
