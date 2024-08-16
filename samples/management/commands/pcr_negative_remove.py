from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from samples.models import CaptureLayout, CaptureOrShotgunPlate, PCR_NEGATIVE, SequencingRun, SequencedLibrary
from django.db import transaction

class Command(BaseCommand):
	help = 'Remove the PCR negative for a sequencing run and its corresponding capture/shotgun batches if no indices are present. Originally written for tweaking a single-stranded batch'

	def add_arguments(self, parser):
		parser.add_argument("sequencing_run")

	def handle(self, *args, **options):
		with transaction.atomic():
			sequencing_run = SequencingRun.objects.get(name=options['sequencing_run'])
			sequenced_libraries = SequencedLibrary.objects.filter(sequencing_run=sequencing_run, indexed_library__p5_index=None, indexed_library__p7_index=None, indexed_library__control_type__control_type=PCR_NEGATIVE)
			for sequenced_library in sequenced_libraries:
				self.stdout.write(str(sequenced_library.id))
				capture_layout = sequenced_library.indexed_library
				self.stdout.write(f'{capture_layout.id}\t{capture_layout.p5_index}\t{capture_layout.p7_index}\t{capture_layout.control_type.control_type}')
				sequenced_library.delete()
				capture_layout.delete()
