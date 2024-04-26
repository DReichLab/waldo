from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.db import transaction

from samples.models import PowderSample, ExtractionBatchLayout, Extract

import re

class Command(BaseCommand):
	help = "File input to add powder amounts for extract layout direct powder sample"
	
	def add_arguments(self, parser):
		parser.add_argument('lysate_ny', help='file containing powder amounts')
		
	def handle(self, *args, **options):
		# read powder information from lysate file
		with transaction.atomic():
			with open(options['lysate_ny']) as f:
				for line in f:
					fields = re.split('\t|\n' line)
					powder_id_str = fields[2]
					powder_id = fields[3]
					extract_id_str = fields[4]
					extract_id = int(fields[5])
					extract_layout_id = int(fields[6])
					control_type = fields[7]
					powder_used1 = fields[8]
					powder_used2 = fields[9]

					if powder_used1 != powder_used2:
						raise ValueError(f'powder used mismatch {powder_used1} {powder_used2}')
					if len(powder_id_str) > 0:
						powder_sample = PowderSample.objects.get(powder_sample_id=powder_id_str, pk=int(powder_id))
						extract = Extract.objects.get(extract_id=extract_id_str, pk=extract_id)
						extract_layout_element = ExtractionBatchLayout.objects.get(pk=extract_layout_id, lysate=None, powder_sample=powder_sample, extract=extract)
						extract_layout_element.powder_used_mg = float(powder_used1)
						extract_layout_element.clean()
						extract_layout_element.save()
