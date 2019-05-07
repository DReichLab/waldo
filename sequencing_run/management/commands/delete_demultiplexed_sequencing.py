from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from sequencing_run.models import DemultiplexedSequencing

class Command(BaseCommand):
	help = 'Remove the demultiplexed sequencing associated with an analysis run'
	
	def add_arguments(self, parser):
		parser.add_argument('--name', required=True)
		parser.add_argument('--date_string', required=True)
		
	def handle(self, *args, **options):
		name = options['name']
		date_string = options['date_string']
		
		string_in_path = '{}_{}'.format(date_string, name)
		to_delete = DemultiplexedSequencing.objects.filter(path__contains=string_in_path)
		# remove many to many entries for flowcells
		for sequencing in to_delete:
			#print(str(sequencing))
			sequencing.flowcells.clear()
		to_delete.delete()
