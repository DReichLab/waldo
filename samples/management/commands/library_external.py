from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from samples.models import get_wetlab_staff, Sample, Library, P5_Index, P7_Index, Barcode

import re

class Command(BaseCommand):
	help = 'Create an external libraries (without library batch)'
	
	def add_arguments(self, parser):
		parser.add_argument('-u', '--user', nargs='+', required=True, help='Wetlab Staff name or username')
		parser.add_argument('-f', '--file', required=True, help='File containing tab-delimited columns: [1] sample number primary key (not Reich lab ID number), [2] I5 index sequence, [3] I7 index sequence, [4] P5 barcode sequence, [5] P7 barcode sequence, [6] library notes', default='10.1.ssDNA_library_prep_Bravo_v4.2')
		parser.add_argument('-s', '--create_samples', action='store_true', help='Specify negative integers for sample primary key. Matching values get same sample')
		
	def handle(self, *args, **options):
		wetlab_user = get_wetlab_staff(options['user'])
		self.stdout.write(f'User: {wetlab_user.name()}')
		user = wetlab_user.login_user

		sample_negative_to_pk = {}
		with transaction.atomic():
			with open(options['file']) as f:
				for line in f:
					fields = re.split(r'\n|\t', line)
					sample_pk_str = fields[0]
					i5 = fields[1]
					i7 = fields[2]
					p5 = fields[3] 
					p7 = fields[4]
					notes = fields[5]
					sample_pk_file = int(sample_pk_str)
					if sample_pk_file < 0 and options['create_samples']: # sample did not exist before running this command
						if sample_pk_file in sample_negative_to_pk:
							sample_pk = sample_negative_to_pk[sample_pk_file]
							sample = Sample.objects.get(id=sample_pk)
						else:
							sample = Sample()
							sample.assign_reich_lab_sample_number(save_user=user) # also saves
							sample_pk = sample.id
							sample_negative_to_pk[sample_pk_file] = sample_pk
							self.stdout.write(f'Sample created pk: {sample.id}')
					else: # sample already exists
						sample = Sample.objects.get(id=sample_pk_file)
						
					# get index and barcode objects from sequence strings
					i5_obj = P5_Index.objects.get(sequence=i5) if len(i5) > 0 else None
					i7_obj = P7_Index.objects.get(sequence=i7) if len(i7) > 0 else None
					p5_barcode = Barcode.objects.get(sequence=p5) if len(p5) > 0 else None
					p7_barcode = Barcode.objects.get(sequence=p7) if len(p7) > 0 else None
					try:
						library = Library.objects.get(sample=sample, p5_index=i5_obj, p7_index=i7_obj, p5_barcode=p5_barcode, p7_barcode=p7_barcode)
						raise ValueError(f'Library already exists: {line}')
					except Library.DoesNotExist:
						library = Library(sample=sample, p5_index=i5_obj, p7_index=i7_obj, p5_barcode=p5_barcode, p7_barcode=p7_barcode)
						library_count = Library.objects.filter(sample=sample, extract=None).count()
						library.reich_lab_library_number = library_count + 1
						library.reich_lab_library_id = f'S{sample.reich_lab_id:04d}.L{library.reich_lab_library_number}'
						library.notes = notes
						library.save(save_user=user)
						self.stdout.write(library.reich_lab_library_id)
