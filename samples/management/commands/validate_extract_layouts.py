from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.core.exceptions import ValidationError

from samples.models import ExtractionBatchLayout, get_value

class Command(BaseCommand):
	help = "Validate extract batch layout"
	
	def add_arguments(self, parser):
		pass
		
	def handle(self, *args, **options):
		for x in ExtractionBatchLayout.objects.all():
			try:
				x.clean()
			except ValidationError as e:
				fields = [x.id, x.get_sample(), x.control_type, get_value(x, 'extract_batch', 'batch_name'), get_value(x, 'lysate', 'lysate_id'), get_value(x, 'extract', 'extraction_lab'), str(e)]
				self.stderr.write('\t'.join([str(z) for z in fields]))
				#raise e
