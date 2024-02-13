from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db import transaction
from samples.models import Library, Barcode, get_value

class Command(BaseCommand):
	help = 'Inspect barcodes for a library'
	
	def add_arguments(self, parser):
		pass
		
	def handle(self, *args, **options):
		library_ids = Library.objects.all()
		for library in library_ids:
			library_batch_name = get_value(library, 'library_batch', 'name')
			udg = get_value(library, 'udg_treatment')

			p5_label = get_value(library, 'p5_barcode', 'label')
			p5_sequence = get_value(library, 'p5_barcode', 'sequence')
			p7_label = get_value(library, 'p7_barcode', 'label')
			p7_sequence = get_value(library, 'p7_barcode', 'sequence')

			p5_index_label = get_value(library, 'p5_index', 'label')
			p5_index_sequence = get_value(library, 'p5_index', 'sequence')
			p7_index_label = get_value(library, 'p7_index', 'label')
			p7_index_sequence = get_value(library, 'p7_index', 'sequence')

			self.stdout.write('\t'.join([library.reich_lab_library_id, udg, library_batch_name, p5_label, p5_sequence, p7_label, p7_sequence, p5_index_label, p5_index_sequence, p7_index_label, p7_index_sequence]))
