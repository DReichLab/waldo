from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from samples.models import CaptureLayout, CaptureOrShotgunPlate, PCR_NEGATIVE, P5_Index, P7_Index

class Command(BaseCommand):
	help = 'Set the PCR negative indices for a capture. Originally written for tweaking a single-stranded batch'

	def add_arguments(self, parser):
		parser.add_argument("capture_batch_name")
		parser.add_argument("i5")
		parser.add_argument("i7")

	def handle(self, *args, **options):
		capture = CaptureOrShotgunPlate.objects.get(name=options['capture_batch_name'])
		pcr_negative = CaptureLayout.objects.get(capture_batch=capture, control_type__control_type=PCR_NEGATIVE)
		pcr_negative.p5_index = P5_Index.objects.get(label=options['i5'])
		pcr_negative.p7_index = P7_Index.objects.get(label=options['i7'])
		pcr_negative.save()
