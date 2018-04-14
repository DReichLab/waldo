from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.utils import timezone
import datetime
from sequencing_run.models import SequencingRun, SequencingAnalysisRun

class Command(BaseCommand):
	help = 'reset the slurm job number for an analysis run'
	
	def add_arguments(self, parser):
		parser.add_argument('--date_string', nargs=1)
		parser.add_argument('--name', nargs=1)
		parser.add_argument('--job', nargs=1)
		
	def handle(self, *args, **options):
		date_string = options['date_string'][0]
		name = options['name'][0]
		date = datetime.datetime.strptime(date_string, "%Y%m%d").date()
		job_number = int(options['job'][0])
		
		run_entry = SequencingAnalysisRun.objects.get(
			name = name,
			sequencing_date = date
		)
		run_entry.slurm_job_number = job_number
		run_entry.save()
