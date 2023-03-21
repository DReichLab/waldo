from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db import transaction
from samples.models import Barcode, P5_Index, P7_Index

def add_barcodes_file(barcodes_file):
	with open(barcodes_file) as f:
		for line in f:
			fields = line.split()
			sequence_set_string = fields[0]
			label = fields[1]

			print(label, sequence_set_string)
			barcode, created = Barcode.objects.get_or_create(label=label, sequence=sequence_set_string)
			barcode.full_clean()

			sublabels = fields[2:]

			if ':' in sequence_set_string:
				individual_sequences = sequence_set_string.split(':')
				for (sublabel, individual_sequence) in zip(sublabels, individual_sequences):
					print(sublabel, individual_sequence)
					barcode, created = Barcode.objects.get_or_create(label=sublabel, sequence=individual_sequence)
					barcode.full_clean()

class Command(BaseCommand):
	help = 'import barcodes from file'
	
	def add_arguments(self, parser):
		parser.add_argument("barcodes_file", nargs='+')
		
	def handle(self, *args, **options):
		barcodes_files = options['barcodes_file']

		with transaction.atomic():
			for barcodes_file in barcodes_files:
				add_barcodes_file(barcodes_file)
