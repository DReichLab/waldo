from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.utils import timezone
import datetime
from sequencing_run.analysis import start_analysis

class Command(BaseCommand):
	help = 'start an analysis from the command line, optionally skipping copy of the illumina directory (assumed manual external copy)'
	
	def add_arguments(self, parser):
		parser.add_argument('--date_string')
		parser.add_argument('--name', nargs='+')
		parser.add_argument('--illumina_directory')
		parser.add_argument('--demultiplex', type=int, default=150)
		parser.add_argument('--skip_copy', action='store_false')
		parser.add_argument('--hold', action='store_true')
		
	def handle(self, *args, **options):
		date_string = options['date_string']
		sequencing_run_names = options['name']
		sequencing_date = datetime.datetime.strptime(date_string, "%Y%m%d").date()
		source_illumina_dir = options['illumina_directory']
		number_top_samples_to_demultiplex = options['demultiplex']
		copy = options['skip_copy']
		hold = options['hold']
		
		combined_sequencing_run_name = '_'.join(sequencing_run_names)
		
		start_analysis(source_illumina_dir, combined_sequencing_run_name, sequencing_date, number_top_samples_to_demultiplex, sequencing_run_names, copy, hold)
