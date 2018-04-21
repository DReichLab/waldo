from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
import datetime
from sequencing_run.ssh_command import ssh_command
from sequencing_run.analysis import index_barcode_keys_used
from sequencing_run.models import SequencingAnalysisRun

class Command(BaseCommand):
	help = 'Create index barcode key file mapping to library ids from database for specified sequencing run'
	
	def add_arguments(self, parser):
		parser.add_argument('--date_string', nargs=1)
		parser.add_argument('--name', nargs=1)
		
	def handle(self, *args, **options):
		date_string = options['date_string'][0]
		name = options['name'][0]
		date = datetime.datetime.strptime(date_string, "%Y%m%d").date()
		
		analysis_run = SequencingAnalysisRun.objects.get(name=name, sequencing_date=date)
		sequencing_run_ids = list(analysis_run.sample_set_names.all())
		separate_sequencing_run_names = [run.name for run in sequencing_run_ids]
		#print(names)
		index_barcode_keys_used(date_string, name, separate_sequencing_run_names)
