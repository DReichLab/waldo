from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

import datetime

from sequencing_run.models import SequencingAnalysisRun

class Command(BaseCommand):
	help = 'Remove analysis sequencing run and its associated records'
	
	def add_arguments(self, parser):
		parser.add_argument('-n', '--name', required=True, help='Remove analysis run with this name.')
		parser.add_argument('-d', '--date_string', required=True, help='Remove analysis run with this date. Other dates are unaffected.')
		parser.add_argument('--dry_run', action='store_true')
		
	def handle(self, *args, **options):
		name = options['name']
		date_string = options['date_string']
		date = datetime.datetime.strptime(date_string, "%Y%m%d").date()
		
		analysis_run = SequencingAnalysisRun.objects.get(name=name, sequencing_date=date)
		s = f'{analysis_run.id}: {str(analysis_run.name)}'
		self.stdout.write(s)
		if not options['dry_run']:
			analysis_run.triggering_flowcells.clear()
			analysis_run.prior_flowcells_for_analysis.clear()
			analysis_run.delete()
