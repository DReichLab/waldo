from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
import datetime
from sequencing_run.ssh_command import ssh_command
from sequencing_run.analysis import replace_parameters, get_scratch_directory
from sequencing_run.models import SequencingAnalysisRun

class Command(BaseCommand):
	help = 'Fill in template parameters to produce WDL json or shell script'
	
	def add_arguments(self, parser):
		parser.add_argument('--date_string', required=True)
		parser.add_argument('--name', required=True)
		parser.add_argument('--source_filename', required=True)
		parser.add_argument('--command_label', required=True)
		parser.add_argument('--shotgun', action='store_true')
		
	def handle(self, *args, **options):
		date_string = options['date_string']
		name = options['name']
		date = datetime.datetime.strptime(date_string, "%Y%m%d").date()
		source_filename = options['source_filename']
		command_label = options['command_label']
		
		analysis_run = SequencingAnalysisRun.objects.get(name=name, sequencing_date=date)
		scratch_illumina_directory_path = "{}/{}_{}/{}".format(get_scratch_directory(), date_string, name, analysis_run.sequencing_run.illumina_directory)
		#print(scratch_illumina_directory_path)
		
		additional_replacements = {}
		if(options['shotgun']):
			additional_replacements[settings.HUMAN_REFERENCE] = settings.SHOTGUN_HUMAN_REFERENCE
			additional_replacements[settings.DEMULTIPLEXED_PARENT_DIRECTORY] = settings.DEMULTIPLEXED_BROAD_SHOTGUN_PARENT_DIRECTORY
		#self.stderr.write(str(additional_replacements))
		
		# TODO This is missing some optional shotgun and threshold read parameters
		# TODO this does not handle options for indices or threshold reads
		
		replace_parameters(source_filename, command_label, name, date_string, scratch_illumina_directory_path, analysis_run.id, analysis_run.top_samples_to_demultiplex, additional_replacements=additional_replacements)

