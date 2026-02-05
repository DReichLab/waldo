from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db import transaction
from samples.models import P5_Index, P7_Index

class Command(BaseCommand):
	help = 'import indices from file'
	
	def add_arguments(self, parser):
		parser.add_argument("type", choices=['i5', 'i7'])
		parser.add_argument("barcodes_file", help='text file with two columns: label and sequence')
		parser.add_argument('-d', "--default",  action='store_true', help='new indices will be part of default set')
		parser.add_argument('--allow_existing',  action='store_true', help='Do not fail if an index already exists')
		parser.add_argument('--label2',  action='store_true', help='File contains a third column for label2')
		
	def handle(self, *args, **options):
		barcode_type = options['type']
		barcodes_file = options['barcodes_file']
		default = options['default']
		
		if barcode_type == 'i5':
			barcodes = P5_Index.objects
		elif barcode_type == 'i7':
			barcodes = P7_Index.objects

		with transaction.atomic():
			num_existing = 0
			with open(barcodes_file) as f:
				for line in f:
					fields = line.split()
					label = fields[0]
					sequence = fields[1]
					label2 = fields[2] if options['label2'] else ''
					try:
						barcode = barcodes.get(sequence=sequence)
						self.stderr.write(f'{sequence} exists as {barcode.label} {barcode.label2}, new is {label}')
						num_existing += 1
					except (P5_Index.DoesNotExist, P7_Index.DoesNotExist):
						barcode = barcodes.create(label=label, sequence=sequence, reich_lab_default=default, label2=label2)
					barcode.full_clean()
				if num_existing > 0 and not options['allow_existing']:
					transaction.set_rollback(True)
