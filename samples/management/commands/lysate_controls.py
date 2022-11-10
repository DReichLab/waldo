from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

import argparse, sys

from samples.models import Lysate, LysateBatch, LysateBatchLayout, get_value

class Command(BaseCommand):
	help = "inspect lysate batch controls"
	
	def add_arguments(self, parser):
		parser.add_argument('lysate_batch')
		
	def handle(self, *args, **options):
		lysate_batch = LysateBatch.objects.get(batch_name=options['lysate_batch'])
		for control in LysateBatchLayout.objects.filter(lysate_batch=lysate_batch, control_type__isnull=False):
			self.stdout.write(f'{control} {control.control_type.control_type}')
