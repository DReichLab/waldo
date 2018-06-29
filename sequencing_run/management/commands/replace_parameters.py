from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
import datetime
from sequencing_run.ssh_command import ssh_command
from sequencing_run.analysis import replace_parameters
from sequencing_run.models import SequencingAnalysisRun

class Command(BaseCommand):
	help = 'Fill in template parameters to produce WDL json or shell script'
	
	def add_arguments(self, parser):
		parser.add_argument('--date_string')
		parser.add_argument('--name')
		parser.add_argument('--source_filename')
		parser.add_argument('--command_label')
		
	def handle(self, *args, **options):
		date_string = options['date_string']
		name = options['name']
		date = datetime.datetime.strptime(date_string, "%Y%m%d").date()
		source_filename = options['source_filename']
		command_label = options['command_label']
		
		analysis_run = SequencingAnalysisRun.objects.get(name=name, sequencing_date=date)
		scratch_illumina_directory_path = "{}/{}_{}/{}".format(settings.SCRATCH_PARENT_DIRECTORY, date_string, name, analysis_run.sequencing_run.illumina_directory)
		#print(scratch_illumina_directory_path)
		
		replace_parameters(source_filename, command_label, name, date_string, scratch_illumina_directory_path, analysis_run.id, analysis_run.top_samples_to_demultiplex)
