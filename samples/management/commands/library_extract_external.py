from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from samples.models import get_wetlab_staff, Extract, Library, P5_Index, P7_Index, Barcode

import re

class Command(BaseCommand):
	help = 'Create an external libraries (without library batch) for an internal extract. '
	
	def add_arguments(self, parser):
		parser.add_argument('-u', '--user', nargs='+', required=True, help='Wetlab Staff name or username')
		parser.add_argument('-f', '--file', required=True, help='File containing tab-delimited columns: [1] extract ID, [2] I5 index sequence, [3] I7 index sequence, [4] P5 barcode sequence, [5] P7 barcode sequence, [6] library notes')
		
	def handle(self, *args, **options):
		wetlab_user = get_wetlab_staff(options['user'])
		self.stdout.write(f'User: {wetlab_user.name()}')
		user = wetlab_user.login_user

		sample_negative_to_pk = {}
		with transaction.atomic():
			with open(options['file']) as f:
				for line in f:
					fields = re.split(r'\n|\t', line)
					extract_id = fields[0]
					i5 = fields[1]
					i7 = fields[2]
					p5 = fields[3] 
					p7 = fields[4]
					notes = fields[5]
					extract = Extract.objects.get(extract_id=extract_id)
						
					# get index and barcode objects from sequence strings
					i5_obj = P5_Index.objects.get(sequence=i5) if len(i5) > 0 else None
					i7_obj = P7_Index.objects.get(sequence=i7) if len(i7) > 0 else None
					p5_barcode = Barcode.objects.get(sequence=p5) if len(p5) > 0 else None
					p7_barcode = Barcode.objects.get(sequence=p7) if len(p7) > 0 else None
					try:
						library = Library.objects.get(extract=extract, p5_index=i5_obj, p7_index=i7_obj, p5_barcode=p5_barcode, p7_barcode=p7_barcode)
						raise ValueError(f'Library already exists: {line}')
					except Library.DoesNotExist:
						library = Library(extract=extract, sample=extract.sample, p5_index=i5_obj, p7_index=i7_obj, p5_barcode=p5_barcode, p7_barcode=p7_barcode)
						library_count = extract.num_libraries()
						if library_count != extract.highest_library():
							raise ValueError('mismatch on number of libraries and max library number')
						library.reich_lab_library_number = library_count + 1
						library.reich_lab_library_id = f'{extract.extract_id}.L{library.reich_lab_library_number}'
						library.notes = notes
						library.save(save_user=user)
						self.stdout.write(library.reich_lab_library_id)
