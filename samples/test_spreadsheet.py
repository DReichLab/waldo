from django.test import SimpleTestCase
from django.core.exceptions import ValidationError

from .spreadsheet import *

class SpreadsheetTest(SimpleTestCase):
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
