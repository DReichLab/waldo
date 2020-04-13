from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from samples.models import Library
from samples.pipeline import load_pipeline_report

class Command(BaseCommand):
	help = 'Load a pipeline analysis report and store results in database'
	
	def add_arguments(self, parser):
		parser.add_argument('-r', '--report', required=True)
		parser.add_argument('-l', '--release_version_label', required=True)
		parser.add_argument('-n', '--sequencing_run_name', required=True)
		parser.add_argument('-e', '--experiment', default='1240k')
		
	def handle(self, *args, **options):
		report_filename = options['report']
		experiment = options['experiment']
		release_version_label = options['release_version_label']
		sequencing_run_name = options['sequencing_run_name']
		
		load_pipeline_report(report_filename, experiment, release_version_label, sequencing_run_name)
