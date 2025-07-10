from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db import transaction

import argparse, sys
import re

from samples.models import Sample, Extract

class Command(BaseCommand):
	help = "For samples by primary key, generate new extract IDs with Reich Lab sample numbers. This is intended for external extracts that arrive from collaborators. "
	
	def add_arguments(self, parser):
		parser.add_argument('samples', type=int, nargs='+', help='Sample primary keys for which to assign Reich Lab sample numbers and create extract')
		parser.add_argument('-l', '--lab', required=True, help='Lab that performed extraction')
		
	def handle(self, *args, **options):
		with transaction.atomic():
			for sample_pk in options['samples']:
				sample = Sample.objects.get(id=sample_pk)
				if sample.reich_lab_id:
					self.stderr.write(f'sample pk {sample_pk} already has Reich lab number {sample.reich_lab_id}')
				extract = sample.originating_extract(options['lab'])
				self.stdout.write('\t'.join([sample.collaborator_code, sample.skeletal_code, extract.extract_id]))
			
