from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
import datetime
from sequencing_run.ssh_command import ssh_command
from sequencing_run.assemble_libraries import prepare_to_assemble_libraries

class Command(BaseCommand):
	help = 'Generate a list of bam files to assemble into candidate library bams'
	
	def add_arguments(self, parser):
		parser.add_argument('--date_string')
		parser.add_argument('--name')
		# Positional arguments
		parser.add_argument('flowcell_text_ids', nargs='+')
		
	def handle(self, *args, **options):
		date_string = options['date_string']
		name = options['name']
		date = datetime.datetime.strptime(date_string, "%Y%m%d").date()
		
		flowcell_text_ids = options['flowcell_text_ids']
		
		prepare_to_assemble_libraries(date_string, name, flowcell_text_ids)
