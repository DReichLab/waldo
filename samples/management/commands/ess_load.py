from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db import transaction
from samples.models import Library, P5_Index, P7_Index, Barcode, CaptureOrShotgunPlate, SequencingRun, LibraryBatch, CaptureLayout, ControlType, PCR_NEGATIVE, CAPTURE_POSITIVE, CAPTURE_POSITIVE_LIBRARY_NAME_DS
from samples.spreadsheet import *
from samples.layout import plate_location, location_from_indices

def field_check(library, field_name, value, update):
	existing_value = getattr(library, field_name)
	if existing_value == None or existing_value == '':
		if update:
			setattr(library, field_name, value)
	elif existing_value != value:
		raise ValueError(f'Library {field_name} mismatch for {library.reich_lab_library_id} [{existing_value}] [{value}]')

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

class Command(BaseCommand):
	help = 'Check/Load extended sample sheet (ESS) file from tab-delimited file into database. This fails if there is inconsistent (present but different) data. '
	
	def add_arguments(self, parser):
		parser.add_argument('ess', help='Tab-delimited extended sample sheet file')
		parser.add_argument('sequencing_run', help='name of sequencing run in database for sample sheet')
		parser.add_argument('-u', '--update', action='store_true', help='Fill in blank data with fields from ESS')
		parser.add_argument('--allow_no_dnu', action='store_true', help='Allow no DNU field when processing a sample sheet')
		parser.add_argument('--dnu', nargs='*', help='Series of strings to identify "Do Not Use" header')
		parser.add_argument('--allow_no_notes', action='store_true', help='Allow no wetlab notes field when processing a sample sheet')
		parser.add_argument('--notes', nargs='*', help='Series of strings to identify "wetlab_notes" header')
		
	def handle(self, *args, **options):
		ess_file = options['ess']
		sequencing_run_str = options['sequencing_run']
		update = options['update']
		
		with open(ess_file) as f:
			headers, data_rows = spreadsheet_headers_and_data_row_fields(f)

		sequencing_run = SequencingRun.objects.get(name=sequencing_run_str)

		capture_positive = ControlType.objects.get(control_type=CAPTURE_POSITIVE)
		pcr_negative = ControlType.objects.get(control_type=PCR_NEGATIVE)

		dnu_header = do_not_use_label(headers, options['dnu'])
		if dnu_header is None and not options['allow_no_dnu']:
			raise ValueError('Do_Not_Use -like header not found and required unless allow_no_dnu is set')
		self.stderr.write(f'DNU header: {dnu_header}')
		notes_header = notes_label(headers, options['notes'])
		if notes_header is None and not options['allow_no_notes']:
			raise ValueError('wetlab_notes -like header not found and required unless allow_no_notes is set')
		self.stderr.write(f'notes header: {notes_header}')

		with transaction.atomic():
			for row in data_rows:
				library_id = get_spreadsheet_value(headers, row, 'Sample_Name')

				i7 = self.barcode_from_str(P7_Index, get_spreadsheet_value(headers, row, 'Index'))
				i5 = self.barcode_from_str(P5_Index, get_spreadsheet_value(headers, row, 'Index2'))

				p5_barcode_str = get_spreadsheet_value(headers, row, 'P5_barcode')
				p5_barcode = self.barcode_from_str(Barcode, p5_barcode_str)

				p7_barcode_str = get_spreadsheet_value(headers, row, 'P7_barcode')
				p7_barcode = self.barcode_from_str(Barcode, p7_barcode_str)

				capture_name =  get_spreadsheet_value(headers, row, 'Capture_Name')
				capture = CaptureOrShotgunPlate.objects.get(name=capture_name)

				try:
					library = Library.objects.get(reich_lab_library_id=library_id)
					control_type = None
					# single-stranded
					if len(i5.sequence) == 8 and len(i7.sequence) == 8:
						if library.library_type != 'ss':
							raise ValueError(f'Library type mismatch for {library_id}')
						field_check(library, 'p5_index', i5, update)
						field_check(library, 'p7_index', i7, update)
						field_check(library, 'p5_barcode', None, False)
						field_check(library, 'p7_barcode', None, False)
					# double-stranded
					elif len(i5.sequence) == 7 and len(i7.sequence) == 7:
						if library.library_type != 'ds':
							raise ValueError(f'Library type mismatch for {library_id}')
						field_check(library, 'p5_index', None, False)
						field_check(library, 'p7_index', None, False)
						field_check(library, 'p5_barcode', p5_barcode, update)
						field_check(library, 'p7_barcode', p7_barcode, update)
					else:
						raise NotImplementedError()

					# experiment in sheet should match capture/shotgun batch
					experiment = get_spreadsheet_value(headers, row, 'Experiment')
					if experiment in ['1240k_plus', '1240K+']:
						experiment = '1240k+'
					if experiment not in capture.protocol.name:
						raise ValueError(f'ESS experiment {experiment} not in capture/shotgun protocol {capture.protocol.name}')

					# library batch
					if 'Batch_id' in headers:
						batch_str = get_spreadsheet_value(headers, row, 'Batch_id')
						library_batch = LibraryBatch.objects.get(name=batch_str)
						field_check(library, 'library_batch', library_batch, update)

					if 'UDG_treatment' in headers:
						udg = get_spreadsheet_value(headers, row, 'UDG_treatment').lower()
						partial_values = ['half', 'partial', 'user']
						library_udg = library.udg_treatment.lower()

						if library_udg == '':
							if update:
								if udg == 'user':
									udg = udg.upper()
								library.udg_treatment = udg
						elif not((udg in partial_values and library_udg in partial_values) or udg == library_udg):
							raise ValueError(f'udg mismatch {library.reich_lab_library_id} [{library_udg}] [{udg}]')

					if 'Library_Style' in headers:
						library_style = get_spreadsheet_value(headers, row, 'Library_Style')
						field_check(library, 'library_type', library_style, update)
				except Library.DoesNotExist:
					library = None
					if library_id == 'Contl.PCR':
						control_type = pcr_negative
					elif library_id == 'Contl.Capture':
						control_type = capture_positive
						library = Library.objects.get(reich_lab_library_id=CAPTURE_POSITIVE_LIBRARY_NAME_DS)
					else:
						raise ValueError(f'{library_id} not found')

				if update:
					# update capture layout
					layout_element, created = CaptureLayout.objects.get_or_create(capture_batch=capture, library=library, control_type=control_type)

					if library:
						library.save()

					if len(i5.sequence) < 8 and len(i7.sequence) < 8:
						# only set indices for double-stranded libraries
						layout_element.p5_index = i5
						layout_element.p7_index = i7
						capture_row, capture_column = plate_location(location_from_indices(int(i5.label), int(i7.label)))
					elif len(i5.sequence) == 8 and len(i7.sequence) == 8:
						# single stranded
						capture_row, capture_column = plate_location(location_from_indices(i5.label, i7_label))
					else:
						raise NotImplementedError(f'Unexpected index lengths {len(i5.sequence)}, {len(i7.sequence)}')
					layout_element.row = capture_row
					layout_element.column = capture_column
					layout_element.save()

					# assign capture layout to sequencing run
					dnu_value = get_spreadsheet_value(headers, row, dnu_header) if dnu_header else ''
					notes_value = get_spreadsheet_value(headers, row, notes_header) if notes_header else ''
					user = None
					sequencing_run.assign_capture_layout_element(layout_element, user, dnu_value, notes_value)

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
