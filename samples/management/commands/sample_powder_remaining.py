from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from samples.models import get_sample_by_anyid

class Command(BaseCommand):
	help = 'For a list of samples, output expected powder remaining, based on initial powder produced and powder used for lysates and extracts from layouts'
	
	def add_arguments(self, parser):
		parser.add_argument("samples", nargs='*')
		parser.add_argument("-f", '--samples_file', help='file containing list of samples')
		
	def handle(self, *args, **options):
		if options['samples_file']:
			with open(options['samples_file']) as f:
				samples = [line.strip() for line in f]
		else:
			samples = []

		for sample_str in samples + options['samples']:
			sample = get_sample_by_anyid(sample_str)
			remaining = sample.powder_remaining()
			self.stdout.write('\t'.join([sample_str, f'{remaining:.1f}']))
