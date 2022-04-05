from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
import datetime
from sequencing_run.ssh_command import ssh_command
from sequencing_run.analysis import adna2_index_barcode_keys_used, index_barcode_keys_used, barcodes_set, i5_set, i7_set
from sequencing_run.models import SequencingAnalysisRun

class Command(BaseCommand):
	help = 'Create index barcode key file mapping to library ids from database for specified sequencing run'
	
	def add_arguments(self, parser):
		parser.add_argument('--date_string', required=True)
		parser.add_argument('--name', required=True)
		parser.add_argument('--ignore_barcodes', action='store_true')
		parser.add_argument('--mysql_ibk', action='store_true')
		parser.add_argument('--output_dir', default="")
		
	def handle(self, *args, **options):
		date_string = options['date_string']
		name = options['name']
		date = datetime.datetime.strptime(date_string, "%Y%m%d").date()
		ignore_barcodes = options['ignore_barcodes']
		mysql_ibk = options['mysql_ibk']
		output_dir = options['output_dir']
		
		analysis_run = SequencingAnalysisRun.objects.get(name=name, sequencing_date=date)
		sequencing_run_ids = list(analysis_run.sample_set_names.all())
		separate_sequencing_run_names = [run.name for run in sequencing_run_ids]
		#print(names)
		if mysql_ibk:
			index_barcode_keys_used(date_string, name, separate_sequencing_run_names, ignore_barcodes, output_dir)
		else:
			adna2_index_barcode_keys_used(date_string, name, separate_sequencing_run_names, output_dir)
		
		# create barcode file too but only if we're not in output_dir mode
		if output_dir == "":
			barcodes_set(date_string, name, separate_sequencing_run_names)
			i5_set(date_string, name, separate_sequencing_run_names)
			i7_set(date_string, name, separate_sequencing_run_names)
