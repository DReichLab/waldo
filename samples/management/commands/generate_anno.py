from django.core.management.base import BaseCommand, CommandError
from samples.anno import sample_anno
from samples.models import Sample, SID_IID_REGEX
import pathlib
import re
import sys

class Command(BaseCommand):
	help = "Generate David's anno file for a list of IDs"
	
	def add_arguments(self, parser):
		parser.add_argument('ids', help="Newline-delimited text file containing sample/external IDs.", type=pathlib.Path)
		
	def handle(self, *args, **options):
		sample_ids_file = options['ids']
		
		# read in file, two columns, tab-delimited
		# ID	external(1) or blank
		with open(sample_ids_file, 'r') as f:
			for line in f:
				fields = re.split('\t|\n', line)
				sample_id = fields[0]
				is_external = (fields[1] == '1')
		
				if is_external:
					sample = Sample.objects.get(external_id=sample_id)
					output_id = sample_id
				else: # internal
					match = re.fullmatch(SID_IID_REGEX, sample_id)
					sample_id = int(match.groupdict()['sample'])
					sample = Sample.objects.get(reich_lab_id=sample_id, control__length=0)
					output_id = f'S{sample.reich_lab_id}'
				self.stdout.write('\t'.join([output_id] + sample_anno(sample)))
