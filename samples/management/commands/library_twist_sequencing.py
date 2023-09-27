from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from samples.models import Library, CaptureOrShotgunPlate, CaptureLayout, SequencedLibrary, get_value

class Command(BaseCommand):
	help = 'Find any Twist captured library. This will not work correctly for old sequencing unless the ESS has been properly loaded.'
	
	def add_arguments(self, parser):
		pass
		
	def handle(self, *args, **options):
		for plate in CaptureOrShotgunPlate.objects.filter(protocol__name__startswith='Twist'):
			for layout_element in CaptureLayout.objects.filter(capture_batch=plate):
				if layout_element.library:
					library_id = get_value(layout_element, 'library', 'reich_lab_library_id')
					experiment = plate.protocol.name
					sequenced_set = SequencedLibrary.objects.filter(indexed_library=layout_element)

					for sequenced in sequenced_set:
						sequencing_run_name = sequenced.sequencing_run.name
						output_str = '\t'.join([library_id, experiment, plate.name, sequencing_run_name])
						self.stdout.write(output_str)
					if len(sequenced_set) == 0:
						sequencing_run_name = ''
						output_str = '\t'.join([library_id, experiment, plate.name, sequencing_run_name])
						self.stdout.write(output_str)
