from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from samples.models import Library
from samples.pipeline import load_pipeline_report

class Command(BaseCommand):
	help = 'Load a pipeline analysis report and store results in database'
	
	def add_arguments(self, parser):
		parser.add_argument('-r', '--report', required=True)
		parser.add_argument('-s', '--split_lane', help="load reports for 'split-lane' seq runs, if this is set the --report option will expect a split lane report mapping file ", action='store_true')
		parser.add_argument('-l', '--release_version_label', required=True)
		parser.add_argument('-n', '--sequencing_run_name', required=True)
		parser.add_argument('-e', '--experiment', default='twist1.4m')
		
	def handle(self, *args, **options):
		report_filename = options['report']
		split_lane = options['split_lane']
		experiment = options['experiment']
		release_version_label = options['release_version_label']
		sequencing_run_name = options['sequencing_run_name']

		if split_lane:
			with open(f'{report_filename}', 'r') as f:
				reports_to_run = [(x.strip().split('\t')[0], x.strip().split('\t')[1]) for x in f.readlines()]
		else:
			reports_to_run = [(sequencing_run_name, report_filename)]

		for pair in reports_to_run:
			seq_run, report = pair
			load_pipeline_report(report, experiment, release_version_label, seq_run)
