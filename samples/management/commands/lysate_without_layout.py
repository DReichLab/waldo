from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

import argparse, sys

from samples.models import Lysate, LysateBatch, LysateBatchLayout, get_value

class Command(BaseCommand):
	help = "Find Lysate without a LysateBatchLayout"
		
	def handle(self, *args, **options):
		for lysate in Lysate.objects.filter(lysatebatchlayout=None).order_by('sample__reich_lab_id'):
			sample = lysate.sample
			if sample is None or sample.is_control():
				pass
			else:
				self.stderr.write(f'{lysate.lysate_id}\t{get_value(lysate.lysate_batch, "batch_name")}')
			try:
				lysate.clean()
			except:
				self.stderr.write(f'{lysate.lysate_id} failed validation')
