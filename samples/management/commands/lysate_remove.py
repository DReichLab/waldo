from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

import argparse, sys

from samples.models import Lysate, LysateBatch, LysateBatchLayout

class Command(BaseCommand):
	help = "Remove a lysate from lysate batch"
	
	def add_arguments(self, parser):
		parser.add_argument('lysate_id')
		
	def handle(self, *args, **options):
		lysate_id_str = options['lysate_id']
		
		lysate = Lysate.objects.get(lysate_id=lysate_id_str)
		for layout_element in LysateBatchLayout.objects.filter(lysate=lysate):
			self.stdout.write(f'{lysate.lysate_batch.batch_name} {layout_element}')
			layout_element.lysate = None
			layout_element.save()
		lysate.delete()
