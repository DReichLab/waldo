from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from samples.models import LysateBatch

class Command(BaseCommand):
	help = 'delete lysate batch'
	
	def add_arguments(self, parser):
		parser.add_argument("lysate_batch_name")
		
	def handle(self, *args, **options):
		batch_name = options['lysate_batch_name']
		batch = LysateBatch.objects.get(batch_name=batch_name)
		batch.delete()
