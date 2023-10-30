from django.core.management.base import BaseCommand
from django.db import transaction
from samples.models import CaptureOrShotgunPlate, CaptureLayout, PCR_NEGATIVE

import re

class Command(BaseCommand):
	help = 'Remove PCR negative from capture. This was originally written for single-stranded batches.'
	
	def add_arguments(self, parser):
		parser.add_argument("capture_name")
		
	def handle(self, *args, **options):
		capture_name = options['capture_name']
		with transaction.atomic():
			plate = CaptureOrShotgunPlate.objects.get(name=capture_name)
			try:
				pcr_negative = CaptureLayout.objects.get(capture_batch=plate, control_type__control_type=PCR_NEGATIVE)
				pcr_negative.delete()
				self.stdout.write(f'PCR Negative removed in {capture_name}')
			except CaptureLayout.DoesNotExist:
				self.stderr.write(f'No PCR Negative in {capture_name}')
