from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
import datetime
from sequencing_run.models import SequencingAnalysisRun

class Command(BaseCommand):
	help = 'signal that preliminary report is ready'
	
	def add_arguments(self, parser):
		parser.add_argument('--date_string', nargs=1)
		parser.add_argument('--name', nargs=1)
		
	def handle(self, *args, **options):
		date_string = options['date_string'][0]
		name = options['name'][0]
		date = datetime.datetime.strptime(date_string, "%Y%m%d").date()
		
		analysis_run = SequencingAnalysisRun.objects.get(name=name, sequencing_date=date)
		if analysis_run != None:
			# state should only move forward
			analysis_run.processing_state = max( SequencingAnalysisRun.RUNNING_ANALYSIS_PRELIMINARY_REPORT_DONE, analysis_run.processing_state)
			analysis_run.save()
