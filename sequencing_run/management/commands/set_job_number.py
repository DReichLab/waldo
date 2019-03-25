from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.utils import timezone
import datetime
from sequencing_run.models import SequencingRun, SequencingAnalysisRun

class Command(BaseCommand):
	help = 'reset the slurm job number for an analysis run'
	
	def add_arguments(self, parser):
		parser.add_argument('--date_string', required=True)
		parser.add_argument('--name', required=True)
		parser.add_argument('--job', required=True, type=int)
		parser.add_argument('-p', '--processing_state', type=int)
		
	def handle(self, *args, **options):
		date_string = options['date_string']
		name = options['name']
		date = datetime.datetime.strptime(date_string, "%Y%m%d").date()
		job_number = options['job']
		
		run_entry = SequencingAnalysisRun.objects.get(
			name = name,
			sequencing_date = date
		)
		run_entry.slurm_job_number = job_number
		if options['processing_state']:
			run_entry.processing_state = options['processing_state']
		run_entry.save()
