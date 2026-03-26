from django.core.management.base import BaseCommand
from django.db.models import Prefetch
from django.db import transaction

from pathlib import Path
import re

from samples.anno import genetic_analysis_anno_headers, genetic_analysis_anno
from samples.models import DataFileAssignment
from sequencing_run.models import GeneticAnalysis

class Command(BaseCommand):
	help = 'Generate anno file. This filters on assessments, dropping those below the threshold (expected for failures and ignores). Optionally, this will generate only anno file entries for specific IDs. If none are specified, all those meeting threshold will be generated.' 
	
	def add_arguments(self, parser):
		parser.add_argument('-f', '--filter', type=int, default=10, help='Filter on assessments')
		parser.add_argument('--ids', nargs='+', help='Specific genetic IDs to display')
		
	def handle(self, *args, **options):
		filter_threshold = options['filter']
		with transaction.atomic():
			assignments_prefetch = Prefetch(
				'data_instance__datafileassignment_set',
				queryset=DataFileAssignment.objects.select_related('data_file__file_type'),
			)
			entries = (
				GeneticAnalysis.objects.filter(assessment__sort_order__gt=filter_threshold)
				.order_by('id')
				.select_related(
					'data_instance__primary_sample__archaeological_assemblage__site__country',
					'data_instance__primary_sample__collaborator',
					'data_instance__primary_sample__skeletal_element_category',
					'data_instance__primary_sample__special_restriction',
					'assessment',
				)
				.prefetch_related(
					assignments_prefetch,
					'data_instance__primary_sample__periods',
					'data_instance__primary_sample__cultures',
					'data_instance__primary_sample__secondary_collaborators',
				)
			)
			
			if options['ids']:
				entries = entries.filter(genetic_id__in=options['ids'])
			
			headers = genetic_analysis_anno_headers()
			self.stdout.write('\t'.join(headers))
			for entry in entries:
				output_dict = genetic_analysis_anno(entry)
				self.stdout.write('\t'.join([output_dict[h] for h in headers]))
				
			transaction.set_rollback(True)
