from django.test import SimpleTestCase
from django.core.exceptions import ValidationError

from .spreadsheet import *

class SpreadsheetTest(SimpleTestCase):
	spreadsheet_file = 'samples/test/spreadsheet_example'

	def test_header_appending_simple(self):
		header = 'a'
		altered_header = spreadsheet_header_read_only(header)
		self.assertEquals(f'a{HEADER_READ_ONLY_INDICATOR}', altered_header)
		
	def test_header_appending_unchanged(self):
		header = 'a' + HEADER_READ_ONLY_INDICATOR
		altered_header = spreadsheet_header_read_only(header)
		self.assertEquals(header, altered_header)
	
	def test_header_appending_batch(self):
		s = 'abc'
		s_read_only = s + HEADER_READ_ONLY_INDICATOR
		headers = [s, s_read_only]
		altered_headers = spreadsheet_headers_read_only(headers)
		for header in altered_headers:
			self.assertEquals(s_read_only, header)

	def test_exact(self):
		with open(self.spreadsheet_file) as f:
			headers, data_rows = spreadsheet_headers_and_data_row_fields(f)

			row1 = data_rows[0]
			self.assertEqual('1', get_spreadsheet_value(headers, row1, 'a') )
			self.assertEqual('2', get_spreadsheet_value(headers, row1, 'b') )
			self.assertEqual('3', get_spreadsheet_value(headers, row1, 'c-') )

			row2 = data_rows[1]
			self.assertEqual('10', get_spreadsheet_value(headers, row2, 'a') )
			self.assertEqual('20', get_spreadsheet_value(headers, row2, 'b') )
			self.assertEqual('30', get_spreadsheet_value(headers, row2, 'c-') )
