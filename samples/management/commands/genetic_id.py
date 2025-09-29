from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

import argparse

from samples.models import Sample, get_sample_by_anyid, get_wetlab_staff
from sequencing_run.models import GeneticAnalysis

class Command(BaseCommand):
	help = "Inspect GeneticAnalysis-sample pairs"
	
	def add_arguments(self, parser):
		parser.add_argument('-s', '--sample', nargs='+', default=[], help='samples for which to inspect genetic analysis')
		parser.add_argument('-g', '--genetic_id', nargs='+', default=[], help='genetic id to inspect')
		
	def handle(self, *args, **options):
		for sample_str in options['sample']:
			sample = get_sample_by_anyid(sample_str)
			analyses = GeneticAnalysis.objects.filter(data_instance__primary_sample=sample)
			for analysis in analyses:
				self.stdout.write(f'{analysis.id}\t{analysis.genetic_id}\t{str(analysis.data_instance.primary_sample)}')
		
		for genetic_id in options['genetic_id']:
			analysis = GeneticAnalysis.objects.get(genetic_id=genetic_id)
			self.stdout.write(f'{analysis.id}\t{analysis.genetic_id}\t{str(analysis.data_instance.primary_sample)}')
	
