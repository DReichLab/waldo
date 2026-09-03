from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from samples.models import get_sample_by_anyid, Sample, Lysate

class Command(BaseCommand):
	help = 'For a list of samples, output expected powder remaining or lysate reamining, based on initial powder produced and powder used for lysates and extracts from layouts, or lysate used for extract'
	
	def add_arguments(self, parser):
		parser.add_argument("samples", nargs='*')
		parser.add_argument("-f", '--samples_file', help='file containing list of samples')
		parser.add_argument("-a", '--all', action='store_true', help='Output for all Reich Lab samples')
		parser.add_argument("-l", '--lysates', action='store_true', help='output the lysates and lysate remaining instead of powder for sample')
		
	def output_sample(self, sample, do_lysate):
		if do_lysate:
			lysates = Lysate.objects.filter(sample=sample).order_by('reich_lab_lysate_number')
			for lysate in lysates:
				self.sample_lysate(lysate)
		else:
			self.sample_powder(sample)
		
	def sample_powder(self, sample):
		produced = str(sample.powder_produced())
		remaining = sample.powder_remaining()
		if isinstance(remaining, float) or isinstance(remaining, int):
			remaining_str = f'{remaining:.1f}'
		else:
			remaining_str = remaining
		self.stdout.write('\t'.join([str(sample), produced, remaining_str]))
		
	def sample_lysate(self, lysate):
		produced = str(lysate.total_volume_produced)
		remaining = lysate.remaining()
		if isinstance(remaining, float) or isinstance(remaining, int):
			remaining_str = f'{remaining:.1f}'
		else:
			remaining_str = remaining
		self.stdout.write('\t'.join([str(lysate.lysate_id), produced, remaining_str]))
		
	def handle(self, *args, **options):
		if options['all']:
			reich_lab_samples_handled = Sample.objects.filter(reich_lab_id__isnull=False).order_by('reich_lab_id', 'control', 'external_id')
			for sample in reich_lab_samples_handled:
				self.output_sample(sample, options['lysates'])
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
				self.output_sample(sample, options['lysates'])
