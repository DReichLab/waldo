from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.db import transaction

from samples.models import PowderSample, ExtractionBatchLayout

import re

class Command(BaseCommand):
	help = "File input to fix existing extract layouts to have direct powder sample"
	
	def add_arguments(self, parser):
		parser.add_argument('extract_layout_fixes', help='file containing layout element and powder sample info')
		
	def handle(self, *args, **options):
		with transaction.atomic():
			with open(options['extract_layout_fixes']) as f:
				for line in f:
					fields = re.split('\t|\n', line)
					extract_layout_id = int(fields[0])
					powder_id_str = fields[4]

					extract_layout_element = ExtractionBatchLayout.objects.get(id=extract_layout_id)
					powder_sample = PowderSample.objects.get(powder_sample_id=powder_id_str)
					extract_layout_element.lysate = None
					extract_layout_element.powder_sample = powder_sample
					extract_layout_element.save()
					extract_layout_element.clean()
					if extract_layout_element.extract:
						extract_layout_element.extract.clean()
