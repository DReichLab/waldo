import django
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db.models import Q
import datetime
from sequencing_run.models import DemultiplexedSequencing, Flowcell, SequencingAnalysisRun

class Command(BaseCommand):
	help = 'Remove demultiplexed index-barcode bams from a flowcell from database. This is used when a flowcell needs to be reanalyzed with a different sample list.'
	
	def add_arguments(self, parser):
		parser.add_argument('--date_string', required=True)
		parser.add_argument('--name', required=True)
		parser.add_argument('-d', '--dry_run', action='store_true', help='Dry run (do not delete anything)')
		
	def handle(self, *args, **options):
		date_string = options['date_string']
		name = options['name']
		dry_run = options['dry_run']
		date = datetime.datetime.strptime(date_string, "%Y%m%d").date()
		
		#self.stdout.write(str(date))
		
		flowcell = Flowcell.objects.filter(
			Q(input_flowcells__name__exact = name), 
			Q(sequencing_date = date)
		)
		self.stdout.write(str(flowcell))
		
		demultiplexed_sequencing_queryset = DemultiplexedSequencing.objects.filter(flowcells__in = flowcell, path__contains = '{}'.format(name))
		self.stdout.write(str(demultiplexed_sequencing_queryset.count()))
		
		if not dry_run:
			for x in demultiplexed_sequencing_queryset:
				x.flowcells.clear()
				x.library.clear()
				x.delete()
