from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

import argparse, sys

from samples.models import Lysate, LysateBatch, LysateBatchLayout

# This will be obsolete when the Lysate keeps track of its originating LysateBatchLayout (#91), rather than the reference being the other way
class Command(BaseCommand):
	help = "Find Lysate with more than one LysateBatchLayout"
	
	#def add_arguments(self, parser):
		#parser.add_argument('extract')
		
	def handle(self, *args, **options):
		for lysate in Lysate.objects.all():
			layout_elements = LysateBatchLayout.objects.filter(lysate=lysate).order_by('lysate_batch__date')
			if len(layout_elements) > 1:
				batches = "\t".join(layout_element.lysate_batch.batch_name for layout_element in layout_elements)
				self.stderr.write(f'{lysate.lysate_id}\t{batches}')
