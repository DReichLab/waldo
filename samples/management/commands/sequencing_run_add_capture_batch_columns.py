from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from samples.models import CaptureOrShotgunPlate, SequencingRun, CaptureLayout, SequencedLibrary, PCR_NEGATIVE, WetLabStaff

import re

class Command(BaseCommand):
	help = "Add user-specified columns from a capture/shotgun batch to a sequencing run"
	
	def add_arguments(self, parser):
		parser.add_argument('-s', "--sequencing_run", required=True, help='Sequencing run destination')
		parser.add_argument('-b', "--capture_name", required=True, help='Batch source for indexed libraries to add to sequencing run')
		parser.add_argument('-u', '--user', required=True, help='Wetlab user first name')
		parser.add_argument('-c', '--create', action='store_true', help='Create sequencing run object')
		parser.add_argument('columns', nargs='+', help='columns (1-indexed) to add from capture to sequencing run')
		
	def handle(self, *args, **options):
		with transaction.atomic():
			if options['create']:
				sequencing_run = SequencingRun.objects.create(name=options['sequencing_run'])
			else:
				sequencing_run = SequencingRun.objects.get(name=options['sequencing_run'])
			
			name = options['user']
			wetlab_user = WetLabStaff.objects.get(first_name=name)
			user = wetlab_user.login_user

			sequencing_run.add_capture_columns(options['capture_name'], options['columns'], user)

			capture = CaptureOrShotgunPlate.objects.get(name=options['capture_name'])
			capture.needs_sequencing_assessment()
