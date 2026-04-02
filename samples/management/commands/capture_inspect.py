from django.core.management.base import BaseCommand

import argparse

from samples.models import CaptureOrShotgunPlate, get_value

class Command(BaseCommand):
	help = "capture/shotgun batch print elements that require indices to be applied at capture/shotgun stage"
	
	def add_arguments(self, parser):
		parser.add_argument('batch')
		
	def handle(self, *args, **options):
		batch = CaptureOrShotgunPlate.objects.get(name=options['batch'])
		for layout_element in batch.layout_elements():
			if layout_element.control_type == None and get_value(layout_element, 'library', 'library_batch', 'protocol', 'library_type') == 'ds' and (layout_element.p5_index is None or layout_element.p7_index is None):
				self.stdout.write(str(layout_element))
