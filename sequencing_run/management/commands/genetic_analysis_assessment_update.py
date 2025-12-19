from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.contrib.auth.models import User

from pathlib import Path
import re

from samples.intake import genetic_analysis_assessment_headers, genetic_analysis_assessment_intake_update

class Command(BaseCommand):
	help = '' 
	
	def add_arguments(self, parser):
		parser.add_argument('batch_file', help=f'Spreadsheet containing columns: ' + ', '.join(genetic_analysis_assessment_headers))
		parser.add_argument('-u', '--user', help='Login user for modification accounting', required=True)
		
	def handle(self, *args, **options):
		with transaction.atomic():
			user = User.objects.get(username=options['user'])
			with open(options['batch_file']) as f:
				genetic_analysis_assessment_intake_update(f, user)
