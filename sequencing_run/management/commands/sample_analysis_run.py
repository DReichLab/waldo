from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.utils import timezone
import datetime
from sequencing_run.models import SequencingRun, SequencingAnalysisRun

class Command(BaseCommand):
	help = 'create an analysis run entry'
	
	def add_arguments(self, parser):
		parser.add_argument('--date_string', nargs=1)
		parser.add_argument('--name', nargs=1)
		parser.add_argument('--illumina_directory', nargs=1)
		
	def handle(self, *args, **options):
		date_string = options['date_string'][0]
		name = options['name'][0]
		date = datetime.datetime.strptime(date_string, "%Y%m%d").date()
		source_illumina_dir = options['illumina_directory'][0]
		
		run_entry = SequencingAnalysisRun(
			name = name, 
			start = timezone.now(),
			processing_state = SequencingAnalysisRun.STARTED,
			sequencing_run = SequencingRun.objects.get(illumina_directory=source_illumina_dir),
			sequencing_date = date,
			top_samples_to_demultiplex = 120
		)
		run_entry.save()
