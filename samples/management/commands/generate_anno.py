from django.core.management.base import BaseCommand, CommandError
from samples.anno import sample_anno
from samples.models import Sample
import pathlib
import re
import sys

SID_IID_REGEX = re.compile(r'[SI]\d+')

class Command(BaseCommand):
	help = "Generate David's anno file for a list of IDs"
	
	def add_arguments(self, parser):
		parser.add_argument('ids', help="Newline-delimited text file containing sample/external IDs.", type=pathlib.Path)
		
	def handle(self, *args, **options):
		sample_ids_file = options['ids']
		sample_ids = [line.rstrip('\n') for line in open(sample_ids_file, 'r')]

		for sample_id in sample_ids:
			try:
				if re.fullmatch(SID_IID_REGEX, sample_id):
					sample_id = sample_id[1:]
				sample = Sample.objects.filter(control__length=0).get(reich_lab_id=int(sample_id))
				output_id = f'S{sample.reich_lab_id}'
			except (Sample.DoesNotExist, ValueError):
				sample = Sample.objects.get(external_id=sample_id)
				output_id = sample_id
			#except Exception as e:
			#	print('Failure for {}'.format(sample_id, file=sys.stderr)
			#	raise e
			self.stdout.write('\t'.join([output_id] + sample_anno(sample)))
