from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db import transaction
from samples.models import Library, Barcode
from samples.management.commands.import_barcodes import add_barcode
from samples.management.commands.ess_load import field_check

class Command(BaseCommand):
	help = 'Load barcodes for libraries from a file. By default, this will check that populated values match. Missing values are replaced.'
	
	def add_arguments(self, parser):
		parser.add_argument('library_p5_p7_barcodes', help='File with columns for library id, p5 barcode, and p7 barcode')
		parser.add_argument('--override', action='store_true', help='Always replace the values')
		
	def handle(self, *args, **options):
		library_p5_p7_barcodes = options['library_p5_p7_barcodes']
		with open(library_p5_p7_barcodes) as f:
			with transaction.atomic():
				for line in f:
					fields = line.split()
					library_id = fields[0]
					p5_label = fields[1]
					p5_barcode_str = fields[2].upper()
					p7_label = fields[3]
					p7_barcode_str = fields[4].upper()

					p5_barcode = add_barcode(p5_label, p5_barcode_str)
					p7_barcode = add_barcode(p7_label, p7_barcode_str)

					library = Library.objects.get(reich_lab_library_id=library_id)
					if options['override']:
						library.p5_barcode = p5_barcode
						library.p7_barcode = p7_barcode
					else:
						field_check(library, 'p5_barcode', p5_barcode, True)
						field_check(library, 'p7_barcode', p7_barcode, True)
					library.save()
