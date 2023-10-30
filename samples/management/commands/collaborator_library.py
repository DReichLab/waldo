from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

import argparse, sys

from samples.spreadsheet import *
from samples.models import P5_Index, P7_Index, Sample, Library, LibraryBatch, LibraryBatchLayout, LibraryProtocol, get_value, CaptureOrShotgunPlate, CaptureLayout

class Command(BaseCommand):
	help = "Create collaborator libraries from spreadsheet. Assumes sample entries already exist. Assume creating first library for each sample. Heavily customized for Pinhasi libraries"
	
	def add_arguments(self, parser):
		parser.add_argument('library_batch')
		parser.add_argument('spreadsheet')
		parser.add_argument('--capture_batch')
		parser.add_argument('--udg', required=True)
		parser.add_argument('--library_type', choices=['ss', 'ds'], default='ds')
		parser.add_argument('-c', '--collaborator', default='Pinhasi')
		parser.add_argument('-n', '--new_indices', action='store_true')
		
	def handle(self, *args, **options):
		library_protocol = LibraryProtocol.objects.get(name='Library prepared by collaborator')
		library_batch, created = LibraryBatch.objects.get_or_create(name=options['library_batch'], protocol=library_protocol, status=LibraryBatch.CLOSED)
		if not created:
			raise ValueError(f"Library batch {options['library_batch']} already exists")

		capture_batch, created = CaptureOrShotgunPlate.objects.get_or_create(name=options['capture_batch'])

		with open(options['spreadsheet'], 'r') as f:
			headers, data_row_fields = spreadsheet_headers_and_data_row_fields(f)

			udg = options['udg']
			for row in data_row_fields:
				sample = Sample.objects.get(id=int(get_spreadsheet_value(headers, row, 'Reich ID')))
				sample.assign_reich_lab_sample_number()

				library_str = f'S{sample.reich_lab_id}.L1'
				p5_index_label = get_spreadsheet_value(headers, row, 'P5 Index #')
				p5_sequence = get_spreadsheet_value(headers, row, 'P5 Index Sequence')
				try:
					p5 = P5_Index.objects.get(sequence=p5_sequence)
				except P5_Index.DoesNotExist as e:
					if options['new_indices']:
						p5_label = f"{options['collaborator']} {p5_index_label}"
						p5, created = P5_Index.objects.get_or_create(label=p5_label, sequence=p5_sequence)
					else:
						raise e

				p7_index_label = get_spreadsheet_value(headers, row, 'P7 Index #')
				p7_sequence = get_spreadsheet_value(headers, row, 'P7 Index Sequence')
				try:
					p7 = P7_Index.objects.get(sequence=p7_sequence)
				except P7_Index.DoesNotExist as e:
					if options['new_indices']:
						p7_label = f"{options['collaborator']} {p7_index_label}"
						p7, created = P7_Index.objects.get_or_create(label=p7_label, sequence=p7_sequence)
					else:
						raise e

				library_position = get_spreadsheet_value(headers, row, 'Reamp plate position')
				library_row = library_position[0]
				library_column = int(library_position[1:])
				fluidx_plate =  get_spreadsheet_value(headers, row, 'FluidX plate')
				fluidx_tube = get_spreadsheet_value(headers, row, 'FluidX tube ID')

				self.stdout.write(f'{sample.id} {p5_sequence} {p7_sequence}')
				library, created = Library.objects.get_or_create(sample=sample, library_batch=library_batch, reich_lab_library_id=library_str, reich_lab_library_number=1, udg_treatment=udg, library_type=options['library_type'], library_prep_lab=options['collaborator'], p5_index=p5, p7_index=p7, plate_id=fluidx_plate, fluidx_barcode=fluidx_tube)
				LibraryBatchLayout.objects.get_or_create(library_batch=library_batch, library=library, row=library_row, column=library_column)

				# assign to capture
				if options['capture_batch']:
					position_str = get_spreadsheet_value(headers, row, 'well in capture plate')
					if len(position_str) > 0:
						row = position_str[0]
						column = int(position_str[1:])
						capture_layout, created_capture = CaptureLayout.objects.get_or_create(capture_batch=capture_batch, library=library, row=row, column=column)
