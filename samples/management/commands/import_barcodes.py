from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db import transaction
from samples.models import Barcode, P5_Index, P7_Index

# Ensure a barcode with this sequence exists.
# If there is an existing one, existing label is used and argument is ignored.
# sequence string may be single barcode, or multiple ':'-delimited set
def add_barcode(label, sequence_string):
	try:
		barcode = Barcode.objects.get(sequence=sequence_string)
	except Barcode.DoesNotExist:
		barcode = Barcode.objects.create(label=label, sequence=sequence_string)

	barcode.full_clean()

def add_barcodes_file(barcodes_file):
	with open(barcodes_file) as f:
		for line in f:
			fields = line.split()
			sequence_set_string = fields[0]
			label = fields[1]

			print(label, sequence_set_string)
			add_barcode(label, sequence_set_string)

			sublabels = fields[2:]

			if ':' in sequence_set_string:
				individual_sequences = sequence_set_string.split(':')
				for (sublabel, individual_sequence) in zip(sublabels, individual_sequences):
					print(sublabel, individual_sequence)
					add_barcode(sublabel, individual_sequence)

class Command(BaseCommand):
	help = 'import barcodes from file'
	
	def add_arguments(self, parser):
		parser.add_argument("barcodes_file", nargs='+')
		
	def handle(self, *args, **options):
		barcodes_files = options['barcodes_file']

		with transaction.atomic():
			for barcodes_file in barcodes_files:
				add_barcodes_file(barcodes_file)
