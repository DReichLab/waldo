from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from samples.models import CaptureOrShotgunPlate

class Command(BaseCommand):
	help = 'Delete a capture or shotgun plate.'
	
	def add_arguments(self, parser):
		parser.add_argument("pk")
		parser.add_argument("capture_name")
		
	def handle(self, *args, **options):
		with transaction.atomic():
			pk = options['pk']
			name = options['capture_name']
			plate = CaptureOrShotgunPlate.objects.get(id=pk, name=name)
			plate.delete()

