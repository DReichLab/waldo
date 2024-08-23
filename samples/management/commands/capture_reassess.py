from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from samples.models import CaptureOrShotgunPlate

class Command(BaseCommand):
	help = "Reassess whether capture/shotgun batches need sequencing"
	
	def add_arguments(self, parser):
		parser.add_argument("batches", nargs='+', help='capture or shotgun batches to reassess for whether sequencing is needed. If one library needs sequencing, the batch is assessed to need sequencing.')
		parser.add_argument('-p', '--print', action='store_true', help='print the layout elements that need sequencing')

	def handle(self, *args, **options):
		for batch_name in options['batches']:
			batch = CaptureOrShotgunPlate.objects.get(name=batch_name)
			# with transaction.atomic():
			assessment = batch.needs_sequencing_assessment(options['print'])
			self.stdout.write(f'{batch.name}\t{assessment}')

