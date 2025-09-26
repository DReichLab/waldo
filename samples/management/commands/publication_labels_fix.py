from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db import transaction

import argparse

from samples.models import PublicationLabels, DataInstance, get_sample_by_anyid, Sample
from sequencing_run.models import GeneticAnalysis

class Command(BaseCommand):
	help = "To fix publication label assignments before migration to data instances instead of samples, assign genetic ids and add new labels for other genetic ids"
	
	def add_arguments(self, parser):
		parser.add_argument('fixfile', nargs='*')
		
	def handle(self, *args, **options):
		with transaction.atomic():
			for filename in options['fixfile']:
				with open(filename) as f:
					for line in f:
						fields = line.split()
						pk = int(fields[0])
						label = PublicationLabels.objects.get(id=pk)
						sample = get_sample_by_anyid(fields[1])
						if label.sample != sample:
							raise ValueError(f'sample mismatch {" ".join(fields)}')
						# set current entry
						label.genetic_id = fields[2]
						label.save()
						# create 
						for genetic_id in fields[3:]:
							new_label, created = PublicationLabels.objects.get_or_create(sample=sample, publication=label.publication, individual_id=label.individual_id, group_label=label.group_label, digital_accession_number=label.digital_accession_number, genetic_id=genetic_id)
