from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db import transaction
from samples.models import Library, Barcode, get_value

class Command(BaseCommand):
	help = 'Inspect barcodes for a library'
	
	def add_arguments(self, parser):
		parser.add_argument('library_id', nargs='+', help='Reich Lab library ID')
		
	def handle(self, *args, **options):
		library_ids = options['library_id']
		for library_id in library_ids:
			library = Library.objects.get(reich_lab_library_id=library_id)

			p5_label = get_value(library, 'p5_barcode', 'label')
			p5_sequence = get_value(library, 'p5_barcode', 'sequence')
			p7_label = get_value(library, 'p7_barcode', 'label')
			p7_sequence = get_value(library, 'p7_barcode', 'sequence')
			self.stdout.write('\t'.join([library_id, p5_label, p5_sequence, p7_label, p7_sequence]))
