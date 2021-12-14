from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from samples.models import CaptureOrShotgunPlate, LibraryBatch, LIBRARY_POSITIVE, LIBRARY_NEGATIVE, LibraryBatchLayout, CaptureLayout

class Command(BaseCommand):
	help = 'Add elements of a library plate to a shotgun or capture plate'
	
	def add_arguments(self, parser):
		parser.add_argument("capture_name")
		parser.add_argument("library_batch_name")
		
	def handle(self, *args, **options):
		with transaction.atomic():
			capture_plate = CaptureOrShotgunPlate.objects.get(name=options['capture_name'])
			library_batch = LibraryBatch.objects.get(name=options['library_batch_name'])
			
			# copy from library layout
			to_copy = LibraryBatchLayout.objects.filter(library_batch=library_batch).exclude(control_type__control_type=LIBRARY_POSITIVE)
			for x in to_copy:
				copied = CaptureLayout(capture_batch = capture_plate, 
									row = x.row,
									column = x.column,
									library = x.library,
									control_type = x.control_type
									)
				copied.save()
			# control changes for capture
			# 1. Move library negative in H12 to H9
			library_negatives = CaptureLayout.objects.filter(capture_batch=capture_plate, control_type__control_type=LIBRARY_NEGATIVE).order_by('column', 'row')
			#print(f'{len(library_negatives)} library_negatives')
			for to_move in library_negatives.filter(row='H', column=12):
				to_move.row = 'H'
				to_move.column = 9
				to_move.save()
			capture_plate.check_library_inputs()
