from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from samples.models import CaptureLayout, CaptureOrShotgunPlate, PCR_NEGATIVE, SequencingRun, SequencedLibrary
from django.db import transaction

class Command(BaseCommand):
	help = 'Remove the PCR negative for a sequencing run and its corresponding capture/shotgun batches if no indices are present, or for capture/shotgun batches. Originally written for tweaking a single-stranded batch'

	def add_arguments(self, parser):
		parser.add_argument('-s', "--sequencing_run", nargs='*')
		parser.add_argument('-c', "--capture", nargs='*')

	def handle(self, *args, **options):
		sequencing_runs = options['sequencing_run']
		if sequencing_runs is None:
			sequencing_runs = []
		for sequencing_run in SequencingRun.objects.filter(name__in=sequencing_runs):
			with transaction.atomic():
				sequenced_libraries = SequencedLibrary.objects.filter(sequencing_run=sequencing_run, indexed_library__p5_index=None, indexed_library__p7_index=None, indexed_library__control_type__control_type=PCR_NEGATIVE)
				for sequenced_library in sequenced_libraries:
					self.stdout.write(str(sequenced_library.id))
					capture_layout = sequenced_library.indexed_library
					self.stdout.write(f'{capture_layout.id}\t{capture_layout.p5_index}\t{capture_layout.p7_index}\t{capture_layout.control_type.control_type}')
					sequenced_library.delete()
					capture_layout.delete()

		capture_or_shotgun_batches = options['capture']
		if capture_or_shotgun_batches is None:
			capture_or_shotgun_batches = []
		for capture in CaptureOrShotgunPlate.objects.filter(name__in=capture_or_shotgun_batches):
			with transaction.atomic():
				for to_delete in CaptureLayout.objects.filter(capture_batch=capture, p5_index=None, p7_index=None, control_type__control_type=PCR_NEGATIVE):
					self.stdout.write(f'{to_delete.id}\t{to_delete.p5_index}\t{to_delete.p7_index}\t{to_delete.control_type.control_type}')
					to_delete.delete()
