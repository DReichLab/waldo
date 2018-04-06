from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
import datetime
from sequencing_run.ssh_command import ssh_command
from sequencing_run.report_match_samples import readSampleSheet, relabelSampleLines

class Command(BaseCommand):
	help = 'rewrite report using a sample sheet input'
	
	def add_arguments(self, parser):
		parser.add_argument('--report', nargs=1)
		parser.add_argument('--sample_sheet', nargs=1)
		
	def handle(self, *args, **options):
		report_filename = options['report'][0]
		sample_sheet_filename = options['sample_sheet'][0]
		
		samples_parameters = readSampleSheet(sample_sheet_filename)
		sampleLines = relabelSampleLines(report_filename, samples_parameters)
		for sample in sampleLines:
			self.stdout.write(sample)
