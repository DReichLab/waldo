from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db import transaction
from django.db.models import Count, Q

from pathlib import Path
import re

from samples.anno import genetic_analysis_anno_headers, genetic_analysis_anno
from samples.models import Sample, SpecialRestriction, DataFileType, DataFile, DataInstance, DataFileAssignment, PublicationLabels, Publication, SID_IID_REGEX, AssessmentCategory
from sequencing_run.models import GeneticAnalysis

class Command(BaseCommand):
	help = 'Generate anno file. This filters on assessments, dropping those below the threshold (expected for failures and ignores). Optionally, this will generate only anno file entries for specific IDs. If none are specified, all those meeting threshold will be generated.' 
	
	def add_arguments(self, parser):
		parser.add_argument('-f', '--filter', type=int, default=10, help='Filter on assessments')
		parser.add_argument('--ids', nargs='+', help='Specific IDs to display')
		
	def handle(self, *args, **options):
		with transaction.atomic():
			filter_threshold = options['filter']
			entries = GeneticAnalysis.objects.filter(assessment__sort_order__gt=filter_threshold).order_by('id')
			if options['ids']:
				entries = entries.filter(genetic_id__in=options['ids'])
			
			headers = genetic_analysis_anno_headers()
			self.stdout.write('\t'.join(headers))
			for entry in entries:
				output_dict = genetic_analysis_anno(entry)
				self.stdout.write('\t'.join([output_dict[h] for h in headers]))
				
			transaction.set_rollback(True)
