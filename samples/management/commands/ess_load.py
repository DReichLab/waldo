from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction
from samples.models import Library, P5_Index, P7_Index, Barcode, CaptureOrShotgunPlate, SequencingRun, LibraryBatch, CaptureLayout, ControlType, EXTRACT_NEGATIVE, LIBRARY_NEGATIVE, PCR_NEGATIVE, CAPTURE_POSITIVE, CAPTURE_POSITIVE_LIBRARY_NAME_DS, LibraryBatchLayout, ExtractionBatch, ExtractionBatchLayout, LysateBatch, LysateBatchLayout, parse_sample_string, get_value, SequencedLibrary, control_from_name_string, TimestampedWellPosition
from samples.spreadsheet import *
from samples.layout import plate_location, location_from_indices
from collections import Counter

# raise exception if values do not match and existing value is non-empty
# allow updating of empty values
def field_check(obj, field_name, value, update):
	existing_value = getattr(obj, field_name)
	if existing_value == None or existing_value == '':
		if update:
			setattr(obj, field_name, value)
	elif existing_value != value:
		raise ValueError(f'{obj.__class__.__name__} {field_name} mismatch for {obj.id} [{existing_value}] [{value}]')

# return whether all nontrivial fields are in string, case insensitive
def all_in_string(string, fields_to_check):
	to_query = string.lower()
	if fields_to_check:
		for field in fields_to_check:
			if field.lower() not in to_query:
				return False
		return len(fields_to_check) > 0
	return False

# search through headers to find column header that looks like "do_not_use" and return it
def do_not_use_label(headers, custom_search):
	for header in headers:
		if all_in_string(header, ['do', 'not', 'use']) or all_in_string(header, ['dnu']) or all_in_string(header, custom_search):
			return header
	return None

# search through headers to find column header that looks like "wetlab_notes" and return it
def notes_label(headers, custom_search):
	for header in headers:
		if all_in_string(header, ['wetlab', 'notes']) or all_in_string(header, custom_search):
			return header
	return None

def h9_library_layout(library_batch, command, do_extract_move, do_lysate_move):
	source_position = TimestampedWellPosition()
	source_position.row = 'H'
	source_position.column = 9
	destination_position = TimestampedWellPosition()
	destination_position.row = 'H'
	destination_position.column = 12
	if library_batch.rotated:
		source_position.rotate()
		destination_position.rotate()
	h9_elements = library_batch.layout_elements().filter(row=source_position.row, column=source_position.column).order_by('library__reich_lab_library_id')
	#for element in h9_elements:
	#	command.stdout.write(f'{element.library.reich_lab_library_id}')
	h9_count = h9_elements.count()
	if h9_count > 2:
		raise ValueError(f'too many {str(source_position)} controls to split to {str(destination_position)}')
	elif h9_count == 2:
		moving_element = h9_elements.last()
		moving_element.column = destination_position.column
		moving_element.save()
		# move prior batches
		if do_extract_move and moving_element.extract is not None:
			extract_layout_element = None
			try:
				extract_layout_element = ExtractionBatchLayout.objects.get(extract=moving_element.extract)
				extract_layout_element.column = destination_position.column
				extract_layout_element.save()
			except ExtractionBatchLayout.MultipleObjectsReturned as e:
				command.stdout.write(moving_element.extract)
				raise e
			if do_lysate_move and extract_layout_element is not None and extract_layout_element.lysate is not None:
				lysate_layout_element = LysateBatchLayout.objects.get(lysate=extract_layout_element.lysate)
				lysate_layout_element.column = destination_position.column
				lysate_layout_element.save()

# returns True if locations should be propagated back to extract stage
# can tell lysate based on sample names (SX.Y1.E1.L1 or SX.E1.L1)
def continue_to_extract(library_batch_name):
	# different technicians have different names for batches that start at library stage and do not continue back to extract/lysate
	stop_names = ['Mob', 'Gang', 'Bunch', 'Bushel', 'Squad', 'Peck', 'Horde']
	for name in stop_names:
		if name in library_batch_name:
			return False
	return True

# read entry
class ESS_Entry:
	# read values from ESS file, with multiple possible formats
	def __init__(self, row, headers, sequencing_run, dnu_header, notes_header):
		try: # Zhao ESS
			self.well_location = None
			self.library_well_location = None
			self.library_id = get_spreadsheet_value(headers, row, 'Sample_Name')

			self.i7 = self.barcode_from_str(P7_Index, get_spreadsheet_value(headers, row, 'Index'))
			self.i5 = self.barcode_from_str(P5_Index, get_spreadsheet_value(headers, row, 'Index2'))

			p5_barcode_str = get_spreadsheet_value(headers, row, 'P5_barcode')
			self.p5_barcode = self.barcode_from_str(Barcode, p5_barcode_str)

			p7_barcode_str = get_spreadsheet_value(headers, row, 'P7_barcode')
			self.p7_barcode = self.barcode_from_str(Barcode, p7_barcode_str)

			self.experiment = get_spreadsheet_value(headers, row, 'Experiment')
			capture_name =  get_spreadsheet_value(headers, row, 'Capture_Name')
			self.capture = CaptureOrShotgunPlate.objects.get(name=capture_name)

			self.library_batch = None
			if 'Batch_id' in headers:
				batch_str = get_spreadsheet_value(headers, row, 'Batch_id')
				if batch_str != 'control_library': # leave controls with None library_batch
					self.library_batch = LibraryBatch.objects.get(name=batch_str)

			self.udg = None
			if 'UDG_treatment' in headers:
				self.udg = get_spreadsheet_value(headers, row, 'UDG_treatment').lower()

			self.library_style = None
			if 'Library_Style' in headers:
				self.library_style = get_spreadsheet_value(headers, row, 'Library_Style')

		except ValueError: # WALDO ESS
			self.well_location = get_spreadsheet_value(headers, row, 'well_position-')
			self.library_well_location = get_spreadsheet_value(headers, row, 'well_position_library_batch-plate_id-')
			self.library_id = get_spreadsheet_value(headers, row, 'library_id-')

			self.i7 = self.barcode_from_str(P7_Index, get_spreadsheet_value(headers, row, 'p7_index-'))
			self.i5 = self.barcode_from_str(P5_Index, get_spreadsheet_value(headers, row, 'p5_index-'))

			p5_barcode_str = get_spreadsheet_value(headers, row, 'p5_barcode-')
			self.p5_barcode = self.barcode_from_str(Barcode, p5_barcode_str)

			p7_barcode_str = get_spreadsheet_value(headers, row, 'p7_barcode-')
			self.p7_barcode = self.barcode_from_str(Barcode, p7_barcode_str)

			# infer capture from sequencing run
			self.experiment = get_spreadsheet_value(headers, row, 'experiment-')
			capture_ids = SequencedLibrary.objects.filter(sequencing_run=sequencing_run).values_list('indexed_library__capture_batch', flat=True).distinct()
			self.capture = CaptureOrShotgunPlate.objects.get(id__in=capture_ids, protocol__name__contains=self.experiment)

			batch_str = get_spreadsheet_value(headers, row, 'library_batch-')
			try:
				self.library_batch = LibraryBatch.objects.get(name=batch_str)
			except LibraryBatch.DoesNotExist:
				self.library_batch = None

			self.udg = get_spreadsheet_value(headers, row, 'udg_treatment-').lower()
			self.library_style = get_spreadsheet_value(headers, row, 'library_type-')

		self.dnu_value = get_spreadsheet_value(headers, row, dnu_header) if dnu_header else ''
		self.notes_value = get_spreadsheet_value(headers, row, notes_header) if notes_header else ''

		if self.experiment in ['1240k_plus', '1240K+']:
			self.experiment = '1240k+'
		self.extract_batch = None
		self.lysate_batch = None

	def barcode_from_str(self, class_name, barcode_str):
		if len(barcode_str) == 0 or barcode_str == '..':
			barcode = None
		else:
			try:
				barcode = class_name.objects.get(sequence=barcode_str.upper())
			except class_name.DoesNotExist as e:
				self.stderr.write(f'{barcode_str} not found')
				raise e
		return barcode

# read in a plate, try to determine which Reich Lab sample IDs correspond to extract and library controls
# Expecting to have two sample IDs, extract first
# 1. extract control
# 2. library control
def controls(headers, data_rows):
	control_sample_numbers = {}
	for row in data_rows:
		try:
			library_id = get_spreadsheet_value(headers, row, 'Sample_Name')
		except ValueError:
			library_id = get_spreadsheet_value(headers, row, 'library_id-')
		if not (library_id.startswith('Contl') or library_id == PCR_NEGATIVE or library_id == CAPTURE_POSITIVE or library_id == CAPTURE_POSITIVE_LIBRARY_NAME_DS or library_id.startswith('control')):
			sample_number, control = parse_sample_string(library_id, full=False)
			if len(control) > 0:
				control_sample_numbers[sample_number] = 1
	if len(control_sample_numbers) == 0:
		return None, None # newer controls do not use Reich Lab sample numbers
	elif len(control_sample_numbers) != 2:
		raise ValueError(f'Distinct control numbers: {len(control_sample_numbers)}: {" ".join([str(num) for num in control_sample_numbers])}')
	sorted_control_sample_number = sorted(control_sample_numbers)
	extract_control_sample_number = sorted_control_sample_number[0]
	library_control_sample_number = sorted_control_sample_number[1]
	if extract_control_sample_number + 1 != library_control_sample_number:
		raise ValueError(f'Expecting extract #{extract_control_sample_number} + 1 = library #{library_control_sample_number}')
	return extract_control_sample_number, library_control_sample_number

def all_lysates(headers, data_rows):
	# count libraries starting from lysates (contain Y# in library ID)
	lysate_count = 0
	no_lysate_count = 0
	for row in data_rows:
		library_id = get_spreadsheet_value(headers, row, 'Sample_Name')

def process_row(row, headers, sequencing_run, options, capture_positive, pcr_negative, extract_control_sample_number, library_control_sample_number, dnu_header, notes_header, update, command):

	# parse spreadsheet row into fields
	ess_entry = ESS_Entry(row, headers, sequencing_run, dnu_header, notes_header)
	# perform field checks
	try:
		library = Library.objects.get(reich_lab_library_id=ess_entry.library_id)
		control_type = None
		# single-stranded
		if len(ess_entry.i5.sequence) == 8 and len(ess_entry.i7.sequence) == 8:
			if library.library_type != 'ss':
				raise ValueError(f'Library type mismatch for {ess_entry.library_id}')
			field_check(library, 'p5_index', ess_entry.i5, update)
			field_check(library, 'p7_index', ess_entry.i7, update)
			field_check(library, 'p5_barcode', None, False)
			field_check(library, 'p7_barcode', None, False)
		# double-stranded
		elif len(ess_entry.i5.sequence) == 7 and len(ess_entry.i7.sequence) == 7:
			if library.library_type != 'ds':
				raise ValueError(f'Library type mismatch for {ess_entry.library_id}')
			field_check(library, 'p5_index', None, False)
			field_check(library, 'p7_index', None, False)
			field_check(library, 'p5_barcode', ess_entry.p5_barcode, update)
			field_check(library, 'p7_barcode', ess_entry.p7_barcode, update)
		else:
			raise NotImplementedError()

		# experiment in sheet should match capture/shotgun batch
		if ess_entry.experiment not in ess_entry.capture.protocol.name:
			raise ValueError(f'ESS experiment {ess_entry.experiment} not in capture/shotgun protocol {ess_entry.capture.protocol.name}')

		# library batch
		if ess_entry.library_batch:
			field_check(library, 'library_batch', ess_entry.library_batch, update)

		if ess_entry.udg: # check udg between library and ESS
			udg = ess_entry.udg
			partial_values = ['half', 'partial', 'user']
			library_udg = library.udg_treatment.lower()

			if library_udg == '':
				if update:
					if udg == 'user':
						udg = udg.upper()
					library.udg_treatment = udg
			elif udg != library_udg and not((udg in partial_values and library_udg in partial_values)):
				raise ValueError(f'udg mismatch {library.reich_lab_library_id} [{library_udg}] [{udg}]')

		if ess_entry.library_style:
			field_check(library, 'library_type', ess_entry.library_style, update)

		# new controls are marked in name
		if ess_entry.library_id.startswith('control') or ess_entry.library_id == PCR_NEGATIVE or ess_entry.library_id == CAPTURE_POSITIVE or ess_entry.library_id == CAPTURE_POSITIVE_LIBRARY_NAME_DS:
			control_type = control_from_name_string(ess_entry.library_id)
		# if this is an old-style control, we need to identify type
		# identify extract and library negative controls based on sample and plate location
		else:
			sample, control_letter = parse_sample_string(ess_entry.library_id, full=False)
			if control_letter:
				if sample == extract_control_sample_number:
					control_type = ControlType.objects.get(control_type=EXTRACT_NEGATIVE)
				elif sample == library_control_sample_number:
					control_type = ControlType.objects.get(control_type=LIBRARY_NEGATIVE)

	except Library.DoesNotExist:
		library = None
		if ess_entry.library_id == 'Contl.PCR' or ess_entry.library_id==PCR_NEGATIVE:
			control_type = pcr_negative
		elif ess_entry.library_id == 'Contl.Capture' or ess_entry.library_id==CAPTURE_POSITIVE:
			control_type = capture_positive
			library = Library.objects.get(reich_lab_library_id=CAPTURE_POSITIVE_LIBRARY_NAME_DS)
		elif ess_entry.library_id.startswith('control'):
			control_type = control_from_name_string(ess_entry.library_id)
		else:
			raise ValueError(f'{ess_entry.library_id} not found')

	# update capture layout
	layout_element, created = CaptureLayout.objects.get_or_create(capture_batch=ess_entry.capture, library=library, control_type=control_type)

	is_control = False
	if library:
		library.clean()
		library.save()
		try:
			is_control = library.is_control()
		except NotImplementedError as e:
			command.stderr.write(f'{ess_entry.library_id} {library}')
			raise e

	if len(ess_entry.i5.sequence) < 8 and len(ess_entry.i7.sequence) < 8:
		# only set indices for double-stranded libraries
		layout_element.p5_index = ess_entry.i5
		layout_element.p7_index = ess_entry.i7
		capture_row, capture_column = plate_location(location_from_indices(int(ess_entry.i5.label), int(ess_entry.i7.label)))
	elif len(ess_entry.i5.sequence) == 8 and len(ess_entry.i7.sequence) == 8:
		# single stranded
		capture_row, capture_column = plate_location(location_from_indices(ess_entry.i5.label, ess_entry.i7_label))
	else:
		raise NotImplementedError(f'Unexpected index lengths {len(ess_entry.i5.sequence)}, {len(ess_entry.i7.sequence)}')
	layout_element.row = capture_row
	layout_element.column = capture_column
	layout_element.clean()
	layout_element.save()

	# assign capture layout to sequencing run
	user = None
	sequencing_run.assign_capture_layout_element(layout_element, user, ess_entry.dnu_value, ess_entry.notes_value)

	# prior batches: library layout, extract layout, lysate layout
	# extract, lysate, powder used
	if options['update_library_layout'] and control_type != capture_positive and control_type != pcr_negative:
		# find the associated extract
		# layout for library batch is slightly different than for capture due to controls moving
		if library:
			extract = library.extract
			library_layout_element, create_library_layout = LibraryBatchLayout.objects.get_or_create(library_batch=library.library_batch, library=library, control_type=control_type)
			field_check(library_layout_element, 'extract', extract, update)
			library_extract_used = get_value(library, 'ul_extract_used', default=0)
			if library_extract_used is not None and library_extract_used > 0:
				field_check(library_layout_element, 'ul_extract_used', library_extract_used, update)
			library_layout_element.row = capture_row
			library_layout_element.column = capture_column
			library_layout_element.save()

	if options['update_extract_layout'] and control_type != capture_positive and control_type != pcr_negative and continue_to_extract(ess_entry.library_batch.name):
		# library and extract controls have extract entries
		extract = get_value(library, 'extract', default=None)
		extract_batch = get_value(library, 'extract', 'extract_batch', default=None)
		# if lysates exist for this extract, we build layout elements
		# if there is no lysate, attempt to lookup powder
		if extract_batch:
			extract_layout_element = ExtractionBatchLayout.objects.get(extract_batch=extract_batch, extract=extract)
			# check that values for existing layout element match what we expect from ESS
			if extract_layout_element.lysate != extract.lysate:
				raise ValueError(f'{extract.lysate.lysate_id} lysate mismatch')
			if extract_layout_element.extract_batch != extract.extract_batch:
				raise ValueError(f'{str(extract_layout_element.id)} extract batch mismatch')
			if extract_layout_element.control_type != control_type:
				raise ValueError(f'{str(extract_layout_element.id)} control type mismatch')
			# lysis volumes are recorded in layout element
			extract_lysate_used = get_value(extract, 'lysis_volume_extracted', default=0)
			if extract_lysate_used is not None and extract_lysate_used > 0:
				field_check(extract_layout_element, 'lysate_volume_used', extract_lysate_used, update)
			# powder amounts for extracts need to be loaded separately because fake lysates have been removed
			extract_layout_element.row = capture_row
			extract_layout_element.column = capture_column
			extract_layout_element.save()

		elif get_value(control_type, 'control_type') != LIBRARY_NEGATIVE:
			command.stderr.write(f'No extract batch for {ess_entry.library_id}')
		ess_entry.extract_batch = extract_batch

		if options['update_lysate_layout'] and control_type != capture_positive and control_type != pcr_negative and continue_to_extract(ess_entry.library_batch.name):
			lysate = get_value(extract, 'lysate', default=None)
			lysate_batch = get_value(lysate, 'lysate_batch', default=None)
			if lysate_batch:
				lysate_layout_element, created = LysateBatchLayout.objects.get_or_create(lysate_batch=lysate_batch, lysate=lysate)
				lysate_layout_element.row = capture_row
				lysate_layout_element.column = capture_column
				field_check(lysate_layout_element, 'control_type', control_type, update)
				lysate_powder_used = get_value(lysate, 'powder_used_mg', default=0)
				if lysate_powder_used is not None and lysate_powder_used > 0:
					field_check(lysate_layout_element, 'powder_used_mg', lysate_powder_used, update)
				lysate_layout_element.save()
			elif get_value(control_type, 'control_type') != LIBRARY_NEGATIVE:
				command.stderr.write(f'No lysate batch for {ess_entry.library_id}')
			ess_entry.lysate_batch = lysate_batch

	return ess_entry, control_type

class Command(BaseCommand):
	help = 'Check/Load extended sample sheet (ESS) file from tab-delimited file into database. This fails if there is inconsistent (present but different) data. This will not create any Sample, PowderSample, Lysate, Extract, or Library objects, which are assumed to exist already. Layout elements to assign locations may be created.'
	
	def add_arguments(self, parser):
		parser.add_argument('ess', help='Tab-delimited extended sample sheet file')
		parser.add_argument('sequencing_run', help='name of sequencing run in database for sample sheet')
		parser.add_argument('release_version', help='string indicating what Reich Lab release this sequecing run first appeared in')
		parser.add_argument('-u', '--update', action='store_true', help='Fill in blank data with fields from ESS')
		parser.add_argument('--dnu', nargs='*', help='Series of strings to identify "Do Not Use" header')
		parser.add_argument('--notes', nargs='*', help='Series of strings to identify "wetlab_notes" header')
		parser.add_argument('-l', '--update_library_layout', action='store_true', help='')
		parser.add_argument('-e', '--update_extract_layout', action='store_true', help='')
		parser.add_argument('-y', '--update_lysate_layout', action='store_true', help='')
		
	def handle(self, *args, **options):
		ess_file = options['ess']
		sequencing_run_str = options['sequencing_run']
		update = options['update']
		
		with open(ess_file) as f:
			headers, data_rows = spreadsheet_headers_and_data_row_fields(f)

		sequencing_run = SequencingRun.objects.get(name=sequencing_run_str)

		capture_positive = ControlType.objects.get(control_type=CAPTURE_POSITIVE)
		pcr_negative = ControlType.objects.get(control_type=PCR_NEGATIVE)
		library_negative = ControlType.objects.get(control_type=LIBRARY_NEGATIVE)

		dnu_header = do_not_use_label(headers, options['dnu'])
		self.stderr.write(f'DNU header: {dnu_header}')
		notes_header = notes_label(headers, options['notes'])
		self.stderr.write(f'notes header: {notes_header}')

		extract_control_sample_number, library_control_sample_number =  controls(headers, data_rows)
		if extract_control_sample_number:
			self.stderr.write(f'extract control {extract_control_sample_number}')
		if library_control_sample_number:
			self.stderr.write(f'library control {library_control_sample_number}')

		capture_or_shotgun_batches = Counter()
		library_batches = Counter()
		extract_batches = Counter()
		lysate_batches = Counter()
		with transaction.atomic():
			for row in data_rows:
				ess_entry, control_type = process_row(row, headers, sequencing_run, options, capture_positive, pcr_negative, extract_control_sample_number, library_control_sample_number, dnu_header, notes_header, True, self)
				capture_or_shotgun_batches.update([ess_entry.capture])
				if control_type != capture_positive and control_type != pcr_negative:
					library_batches.update([ess_entry.library_batch])
					if ess_entry.extract_batch is not None or control_type != library_negative:
						extract_batches.update([ess_entry.extract_batch])
					if ess_entry.lysate_batch is not None or control_type != library_negative:
						lysate_batches.update([ess_entry.lysate_batch])

			# validate batches
			for capture in capture_or_shotgun_batches:
				self.stdout.write(f'{capture.name}\t{capture_or_shotgun_batches[capture]}')
				capture.clean()
			for library_batch in library_batches:
				self.stdout.write(f'Library batch: {get_value(library_batch, "name")}\t{library_batches[library_batch]}')
				if library_batch is not None:
					# move H9 controls back to H12
					h9_library_layout(library_batch, self, len(extract_batches) > 0, len(lysate_batches) > 0)
					if library_batch:
						try:
							library_batch.clean()
						except ValidationError as e:
							# diagnostic state of failed validation
							for element in library_batch.layout_elements():
								library_id = get_value(element, 'library', 'reich_lab_library_id')
								self.stdout.write(f'{element}\t{library_id}')
							raise e
			# extract and lysate batch validation
			for extract_batch in extract_batches:
				self.stdout.write(f'Extract batch: {get_value(extract_batch, "batch_name")}\t{extract_batches[extract_batch]}')
				if extract_batch is not None:
					extract_batch.clean()
			for lysate_batch in lysate_batches:
				self.stdout.write(f'Lysate batch: {get_value(lysate_batch, "batch_name")}\t{lysate_batches[lysate_batch]}')
				if lysate_batch is not None:
					lysate_batch.clean()

			sequencing_run.reich_lab_release_version = options['release_version']
			sequencing_run.save()
			if not update:
				transaction.set_rollback(True)
