from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
import datetime
from sequencing_run.ssh_command import ssh_command
from sequencing_run.analysis import replace_parameters
from sequencing_run.models import SequencingAnalysisRun

class Command(BaseCommand):
	help = 'Fill in template parameters to produce WDL json or shell script'
	
	def add_arguments(self, parser):
		parser.add_argument('--date_string', nargs=1)
		parser.add_argument('--name', nargs=1)
		parser.add_argument('--source_filename', nargs=1)
		parser.add_argument('--command_label', nargs=1)
		
	def handle(self, *args, **options):
		date_string = options['date_string'][0]
		name = options['name'][0]
		date = datetime.datetime.strptime(date_string, "%Y%m%d").date()
		source_filename = options['source_filename'][0]
		command_label = options['command_label'][0]
		
		scratch_illumina_directory_path = "{}/{}_{}".format(settings.SCRATCH_PARENT_DIRECTORY, date_string, name)
		analysis_run = SequencingAnalysisRun.objects.get(name=name, sequencing_date=date)
		
		replace_parameters(source_filename, command_label, name, date_string, scratch_illumina_directory_path, analysis_run.id, analysis_run.top_samples_to_demultiplex)
