from django.core.management.base import BaseCommand
from django.db import transaction

from pathlib import Path
import re

from samples.anno import (
	genetic_analysis_anno_headers,
	genetic_analysis_anno,
	genetic_analysis_for_anno_queryset,
)

class Command(BaseCommand):
	help = 'Generate anno file. This filters on assessments, dropping those below the threshold (expected for failures and ignores). Optionally, this will generate only anno file entries for specific IDs. If none are specified, all those meeting threshold will be generated.' 
	
	def add_arguments(self, parser):
		parser.add_argument('-f', '--filter', type=int, default=10, help='Filter on assessments')
		parser.add_argument('--ids', nargs='*', help='Specific genetic IDs to display')
		parser.add_argument('--file', help='Specific genetic IDs to display, in a file, one genetic ID per line')
		
	def handle(self, *args, **options):
		filter_threshold = options['filter']
		with transaction.atomic():
			entries = (
				genetic_analysis_for_anno_queryset()
				.filter(assessment__sort_order__gt=filter_threshold)
				.order_by('id')
			)
			
			# filter by the union of IDs from command line and file inputs
			if options['ids'] or options['file']:
				filter_list = []
				if options['ids']:
					filter_list = options['ids']
				if options['file']:
					with open(options['file']) as f:
						filter_list += [x.strip() for x in f]
				
				entries = entries.filter(genetic_id__in=filter_list)
			
			headers = genetic_analysis_anno_headers()
			self.stdout.write('\t'.join(headers))
			for entry in entries:
				output_dict = genetic_analysis_anno(entry)
				self.stdout.write('\t'.join([output_dict[h] for h in headers]))
				
			transaction.set_rollback(True)
