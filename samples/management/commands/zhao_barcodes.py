from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from samples.models import Barcode, P5_Index, P7_Index, Library, LibraryBatch

class BarcodeIssue(Exception):
	pass
	
def barcode_length(sequence):
	if ':' in sequence:
		parts = sequence.split(':')
		lengths = [len(part) for part in parts]
		for to_check in lengths[1:]:
			if lengths[0] != to_check:
				raise ValueError(f'barcode length problem in {sequence}')
		return lengths[0]
	else:
		return len(sequence)

def get_barcode(label, sequence):
	try:
		barcode_object = Barcode.objects.get(sequence=sequence)
	except Barcode.DoesNotExist:
		barcode_object = None
		if len(sequence) != 8:
			raise BarcodeIssue(f'{label} {sequence} barcode not found that is not single-stranded')
	try:
		if barcode_object and label != barcode_object.label:
			q_superset = Barcode.objects.get(label__startswith='Q', sequence__contains=sequence)
			superset_sequence = q_superset.sequence.split(':')
			index = superset_sequence.index(sequence)
			prefix = 'ABCD'
			if label != f'{prefix[index]}{q_superset.label[1:]}':
				raise BarcodeIssue(f'{label} "{sequence}" barcode not found that is not single-stranded')
	except:
		raise BarcodeIssue('label sequence mismatch')
			
	return barcode_object

class Command(BaseCommand):
	help = "import library barcodes from file. Used to import from Zhao's database"
	
	def add_arguments(self, parser):
		parser.add_argument("zhao_file")
		
	def handle(self, *args, **options):
		barcodes_file = options['zhao_file']

		with open(barcodes_file) as f:
			for line in f:
				raw_fields = line.split()
				fields = [x.strip() for x in raw_fields]
				
				library_batch_name = fields[0]
				library_id = fields[1]
				p5_qbarcode_label = fields[2]
				p7_qbarcode_label = fields[3]
				p5_barcode_sequence = fields[4]
				p7_barcode_sequence = fields[5]
				
				try:
					if barcode_length(p5_barcode_sequence) != barcode_length(p7_barcode_sequence):
						raise BarcodeIssue()
					
					library_batch = LibraryBatch.objects.get(name=library_batch_name)
					
					p5 = get_barcode(p5_qbarcode_label, p5_barcode_sequence)
					p7 = get_barcode(p7_qbarcode_label, p7_barcode_sequence)
					
					library = Library.objects.get(library_batch=library_batch, reich_lab_library_id=library_id)
					
					if p5 and p7:
						library.p5_barcode = p5
						library.p7_barcode = p7
						library.clean()
						library.save()
					elif p5 or p7:
						raise ValueError(f'Not expecting only one barcode: {p5_qbarcode_label} {p7_qbarcode_label} {p5_barcode_sequence} {p7_barcode_sequence}')
					
				except LibraryBatch.DoesNotExist: # extract batches are listed for libraries in Zhao's table
					pass
				except (BarcodeIssue, Library.DoesNotExist):
					print(line, end='')
