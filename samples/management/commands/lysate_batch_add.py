from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

import argparse, sys

from samples.models import LysateBatch, LysateBatchLayout, ControlType, EXTRACT_NEGATIVE, PowderSample

class Command(BaseCommand):
	help = "Add a powder or control to a lysate batch"
	
	def add_arguments(self, parser):
		parser.add_argument('lysate_batch')
		parser.add_argument('position')

		group = parser.add_mutually_exclusive_group(required=True)
		group.add_argument('-p', '--powder')
		group.add_argument('-c', '--control', action='store_true')
		
	def handle(self, *args, **options):
		lysate_batch = LysateBatch.objects.get(batch_name=options['lysate_batch'])

		if options['control']:
			control_type = ControlType.objects.get(control_type=EXTRACT_NEGATIVE)
			powder = None
			powder_batch = None
		else:
			control_type = None
			powder = PowderSample.objects.get(powder_sample_id=options['powder'])
			powder_batch = powder.powder_batch

		powder_used_mg = 0 # needs to be set manually in batch

		position_str = options['position']
		row = position_str[0]
		column = int(position_str[1:])

		LysateBatchLayout.objects.get_or_create(lysate_batch=lysate_batch, powder_sample=powder, control_type=control_type, row=row, column=column, powder_used_mg=0)
