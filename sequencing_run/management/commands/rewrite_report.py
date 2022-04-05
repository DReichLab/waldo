from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
import datetime
from sequencing_run.ssh_command import ssh_command
from sequencing_run.report_match_samples import readSampleSheet, relabelSampleLines

class Command(BaseCommand):
	help = 'rewrite report using a sample sheet input'
	
	def add_arguments(self, parser):
		parser.add_argument('--report', required=True)
		parser.add_argument('--sample_sheet', required=True, nargs='+')
		parser.add_argument('--legacy_ess', action='store_true')
		
	def handle(self, *args, **options):
		report_filename = options['report']
		sample_sheet_filenames = options['sample_sheet']
		adna2 = not(options['legacy_ess'])
		
		samples_parameters = {}
		for sample_sheet_filename in sample_sheet_filenames:
			samples_parameters_single = readSampleSheet(sample_sheet_filename, adna2)
			samples_parameters.update(samples_parameters_single)
			
		sampleLines = relabelSampleLines(report_filename, samples_parameters)
		for sample in sampleLines:
			self.stdout.write(sample)
