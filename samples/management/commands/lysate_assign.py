from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db import transaction

import argparse, sys

from samples.models import Lysate, LysateBatch, LysateBatchLayout, get_value, PowderSample

class Command(BaseCommand):
	help = "Assign Lysate without a LysateBatchLayout to a LysateBatch"
	
	def add_arguments(self, parser):
		parser.add_argument('-l', '--lysate', required=True, help='lysate id string, for example: S1234.Y1')
		parser.add_argument('-b', '--lysate_batch', required=True)
		parser.add_argument('-p', '--position')
		parser.add_argument('-w', '--powder', action='store_true', help='infer powder from sample and assign. Fails if there is more than one possibility.')
		
	def handle(self, *args, **options):
		with transaction.atomic():
			lysate = Lysate.objects.get(lysate_id=options['lysate'])
			# correct powder
			if options['powder']:
				powder = PowderSample.objects.get(sample_id=lysate.sample)
				if lysate.powder_sample is not None:
					if lysate.powder_sample != powder:
						raise ValueError(f'Powder mismatch {lysate.powder_sample} {powder}')
				else:
					lysate.powder = powder
					
			lysate_batch = LysateBatch.objects.get(batch_name=options['lysate_batch'])
			if LysateBatchLayout.objects.filter(lysate=lysate).count() > 0:
				raise ValueError('lysate has lysate batch already')
			layout_element = LysateBatchLayout(lysate_batch=lysate_batch, powder_sample=lysate.powder_sample, powder_used_mg=lysate.powder_used_mg, lysate=lysate)
			if options['position']:
				row = options['position'][0]
				column = int(options['position'][1:])
				layout_element.row = row
				layout_element.column = column
			layout_element.save()
			lysate.lysate_batch = lysate_batch
			lysate.clean()
			layout_element.clean()
			lysate.save()
			lysate_batch.clean()
