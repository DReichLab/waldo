from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from samples.models import Sample
from sequencing_run.library_id import LibraryID
from samples.anno import individual_from_library_id

class Command(BaseCommand):
	help = '''Take a .ind file for a pulldown and rewrite it with the following properties:
	1. Replace instance ID with individual ID if this individual's first library. 
	2. Use group name
	'''
	
	def add_arguments(self, parser):
		parser.add_argument('--ind', nargs='+', required=True)
		
	def handle(self, *args, **options):
		ind_filenames = options['ind']
		
		for ind_filename in ind_filenames:
			with open(ind_filename) as f:
				for line in f:
					fields = line.split()
					instance_id_raw = fields[0]
					sex = fields[1]

					#self.stderr.write(instance_id_raw)
					if instance_id_raw.startswith('I'):
						sample_number = int(instance_id_raw.split('_')[0][1:])
						#self.stderr.write(str(sample_number))
					else:
						raise ValueError('Failure for {}'.format(instance_id_raw))
				
					group_label = Sample.objects.get(reich_lab_id__exact=sample_number).group_label
					
					self.stdout.write('{}\t{}\t{}'.format(instance_id_raw, sex, group_label))
