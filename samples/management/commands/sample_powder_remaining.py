from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from samples.models import get_sample_by_anyid, Sample

class Command(BaseCommand):
	help = 'For a list of samples, output expected powder remaining, based on initial powder produced and powder used for lysates and extracts from layouts'
	
	def add_arguments(self, parser):
		parser.add_argument("samples", nargs='*')
		parser.add_argument("-f", '--samples_file', help='file containing list of samples')
		parser.add_argument("-a", '--all', action='store_true', help='Output for all Reich Lab samples')
		
	def output_sample(self, sample):
		produced = str(sample.powder_produced())
		remaining = sample.powder_remaining()
		if isinstance(remaining, float) or isinstance(remaining, int):
			remaining_str = f'{remaining:.1f}'
		else:
			remaining_str = remaining
		self.stdout.write('\t'.join([str(sample), produced, remaining_str]))
		
	def handle(self, *args, **options):
		if options['all']:
			reich_lab_samples_handled = Sample.objects.filter(reich_lab_id__isnull=False).order_by('reich_lab_id', 'control', 'external_id')
			for sample in reich_lab_samples_handled:
				self.output_sample(sample)
		else:
			reich_lab_samples_handled = Sample.objects.none()
			
		if options['samples_file']:
			with open(options['samples_file']) as f:
				samples = [line.strip() for line in f]
		else:
			samples = []

		for sample_str in samples + options['samples']:
			sample = get_sample_by_anyid(sample_str)
			if sample not in (reich_lab_samples_handled):
				self.output_sample(sample)
