from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from samples.models import CaptureLayout

class Command(BaseCommand):
	help = ''
		
	def handle(self, *args, **options):
		capture_positives = CaptureLayout.objects.filter(control_type__control_type='Capture Positive').order_by('capture_batch__date')
		for capture_positive in capture_positives:
			#if capture_positive.library is not None:
			#	raise NotImplementedError()
			print('\t'.join([capture_positive.capture_batch.name, str(capture_positive.capture_batch.date), str(capture_positive.nanodrop)]))
