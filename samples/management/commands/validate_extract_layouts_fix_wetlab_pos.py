from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.db import transaction

from samples.models import ControlType, ExtractionBatch, ExtractionBatchLayout, EXTRACT_NEGATIVE

class Command(BaseCommand):
	help = "Reassign WetLabPos as controls to pass validation"
	
	def add_arguments(self, parser):
		pass
		
	def handle(self, *args, **options):
		with transaction.atomic():
			extract_batch = ExtractionBatch.objects.get(batch_name='WetLabPos')
			assignments = ExtractionBatchLayout.objects.filter(extract_batch=extract_batch)
			other_control, created = ControlType.objects.get_or_create(control_type='other')
			for layout_element in assignments:
				layout_element.control_type = other_control
				layout_element.save()

			layout_element = ExtractionBatchLayout.objects.get(id=5203, extract__extract_id='S6483a.E1')
			extract_control = ControlType.objects.get(control_type=EXTRACT_NEGATIVE)
			layout_element.control_type = extract_control
			layout_element.save()
