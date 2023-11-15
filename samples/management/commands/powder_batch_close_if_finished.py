from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from samples.models import PowderBatch

class Command(BaseCommand):
	help = 'Close a powder batch if all powder samples assigned.'
	
	def add_arguments(self, parser):
		parser.add_argument('powder_batch')
		
	def handle(self, *args, **options):		
		powder_batch = PowderBatch.objects.get(name=options['powder_batch'])
		powder_batch.close_if_finished(True)
