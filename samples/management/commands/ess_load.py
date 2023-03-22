from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db import transaction
from samples.models import Library, P5_Index, P7_Index, Barcode, CaptureOrShotgunPlate, SequencingRun, LibraryBatch, CaptureLayout, ControlType, PCR_NEGATIVE, CAPTURE_POSITIVE, CAPTURE_POSITIVE_LIBRARY_NAME_DS
from samples.spreadsheet import *
from samples.layout import plate_location, location_from_indices

def field_check(library, field_name, value, update):
	existing_value = getattr(library, field_name)
	if existing_value == None:
		if update:
			setattr(library, field_name, value)
	elif existing_value != value:
		raise ValueError(f'Library {field_name} mismatch for {library.reich_lab_library_id} {existing_value} {value}')

class Command(BaseCommand):
	help = 'Load extended sample sheet (ESS) file from tab-delimited file into database'
	
	def add_arguments(self, parser):
		parser.add_argument('ess')
		parser.add_argument('sequencing_run')
		parser.add_argument('-u', '--update', action='store_true')
		
	def handle(self, *args, **options):
		ess_file = options['ess']
		sequencing_run_str = options['sequencing_run']
		update = options['update']
		
		with open(ess_file) as f:
			headers, data_rows = spreadsheet_headers_and_data_row_fields(f)

		sequencing_run = SequencingRun.objects.get(name=sequencing_run_str)

		capture_positive = ControlType.objects.get(control_type=CAPTURE_POSITIVE)
		pcr_negative = ControlType.objects.get(control_type=PCR_NEGATIVE)

		with transaction.atomic():
			for row in data_rows:
				library_id = get_spreadsheet_value(headers, row, 'Sample_Name')

				i7 = P7_Index.objects.get(sequence=get_spreadsheet_value(headers, row, 'Index'))
				i5 = P5_Index.objects.get(sequence=get_spreadsheet_value(headers, row, 'Index2'))

				p5_barcode_str = get_spreadsheet_value(headers, row, 'P5_barcode')
				p5_barcode = self.barcode_from_str(p5_barcode_str)

				p7_barcode_str = get_spreadsheet_value(headers, row, 'P7_barcode')
				p7_barcode = self.barcode_from_str(p7_barcode_str)

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

					# double-stranded
					elif len(i5.sequence) == 7 and len(i7.sequence) == 7:
						if library.library_type != 'ds':
							raise ValueError(f'Library type mismatch for {library_id}')
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
						if not((udg in partial_values and library_udg in partial_values) or udg == library_udg):
							raise ValueError(f'udg mismatch {library.reich_lab_library_id} {library_udg} {udg}')

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
					layout_element.p5_index = i5
					layout_element.p7_index = i7
					if library:
						if library.library_type!='ds':
							raise NotImplementedError()
						library.save()
					capture_row, capture_column = plate_location(location_from_indices(int(i5.label), int(i7.label)))
					layout_element.row = capture_row
					layout_element.column = capture_column
					layout_element.save()
					# assign capture layout to sequencing run
					sequencing_run.assign_capture_layout_element(layout_element)

	def barcode_from_str(self, barcode_str):
		if len(barcode_str) == 0 or barcode_str == '..':
			barcode = None
		else:
			try:
				barcode = Barcode.objects.get(sequence=barcode_str)
			except Barcode.DoesNotExist as e:
				self.stderr.write(f'{barcode_str} not found')
				raise e
		return barcode
