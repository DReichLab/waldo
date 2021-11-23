from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.utils import timezone
import datetime
from sequencing_run.models import SequencingRun, SequencingAnalysisRun
from sequencing_run.analysis import copy_illumina_directory, get_scratch_directory

class Command(BaseCommand):
	help = 'recopy illumina directory for a sequencing run'
	
	def add_arguments(self, parser):
		parser.add_argument('--date_string', nargs=1)
		parser.add_argument('--name', nargs=1)
		
	def handle(self, *args, **options):
		date_string = options['date_string'][0]
		name = options['name'][0]
		date = datetime.datetime.strptime(date_string, "%Y%m%d").date()
		
		run_entry = SequencingAnalysisRun.objects.get(
			name = name,
			sequencing_date = date
		)

		destination_directory = date_string + '_' + name
		scratch_illumina_parent_path = get_scratch_directory() + "/" + destination_directory
		
		illumina_directory = run_entry.sequencing_run.illumina_directory
		copy_illumina_directory(illumina_directory, scratch_illumina_parent_path)
