from samples.models import CaptureOrShotgunPlate, SequencingRun, CaptureLayout, SequencedLibrary
from django.db import transaction

# create sequencing runs for a set of indexed library plates
# this will use columns 1-3, 4-6, 7-9, 10-12 for each of the input plates to create a sequencing run
def create_sequencing_run_four_series(indexed_library_plate_strings, sequencing_run_prefix, user):
	indexed_library_plates = CaptureOrShotgunPlate.objects.filter(name__in=indexed_library_plate_strings)
	with transaction.atomic():
		for index in [1, 2, 3 ,4]:
			create_single_partial_sequencing_run(indexed_library_plates, sequencing_run_prefix, user, index)

def create_single_partial_sequencing_run(indexed_library_plates, sequencing_run_prefix, user, index):
	sequencing_run_name = f'{sequencing_run_prefix}_{str(index)}_SQ'
	sequencing_run = SequencingRun.objects.create(name=sequencing_run_name)
	start = 1 + 3 * (index - 1)
	included_columns = range(start, start+3)
	for plate in indexed_library_plates:
		layout_elements = CaptureLayout.objects.filter(capture_batch=plate, column__in=included_columns)
		for layout_element in layout_elements:
			sequenced_library = SequencedLibrary(indexed_library=layout_element, sequencing_run=sequencing_run)
			sequenced_library.save(save_user=user)
