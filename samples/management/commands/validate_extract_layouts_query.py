from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from samples.models import Lysate, Extract, ExtractionBatchLayout

class Command(BaseCommand):
	help = "Find extract batch layouts involving fake lysates"
	
	def add_arguments(self, parser):
		pass
		
	def handle(self, *args, **options):
		for lysate in Lysate.objects.filter(lysate_id__contains='.NY'):
			for extract in Extract.objects.filter(lysate=lysate):
				try:
					layout_element = ExtractionBatchLayout.objects.get(extract=extract)
					powder = None
					if lysate.powder_sample:
						powder = lysate.powder_sample
					self.stdout.write(f'{layout_element.id}\t{extract.id}\t{extract.extract_id}\t{powder.id}\t{powder.powder_sample_id}')
				except ExtractionBatchLayout.DoesNotExist:
					self.stderr.write(f'{extract.id}\t{extract.extract_id}')
