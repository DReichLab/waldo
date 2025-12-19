import re
import types

DELIMITER = '\t'
HEADER_READ_ONLY_INDICATOR = '-'

utf8_pattern_filter = re.compile('^[\W]+', re.UNICODE)
def spreadsheet_pass(spreadsheet_file, **kwargs):
	if 'delimiter' in kwargs:
		delimiter = kwargs['delimiter']
	else:
		delimiter = DELIMITER
		
	header = spreadsheet_file.readline()
	# the header should contain python variable names, remove leading non alphanumberic + _ characters
	# Mac Excel has added these when exporting UTF8
	try:
		comment_start = b'#'
		header = re.sub(utf8_pattern_filter, '', header.decode('utf-8'), count=1).encode('utf-8')
	except AttributeError:
		comment_start = '#'
	for line in spreadsheet_file:
		if not line.startswith(comment_start):
			row = SpreadsheetRow(header, line, delimiter=delimiter)
			yield row

class SpreadsheetRow():
	def __init__(self, header, data, **kwargs):
		if 'delimiter' in kwargs:
			delimiter = kwargs['delimiter']
		else:
			delimiter = DELIMITER
			
		try:
			trimmed_header = header.rstrip('\r\n')
			trimmed_data = data.rstrip('\r\n')
		except TypeError:
			trimmed_header = header.decode('utf-8').rstrip('\r\n')
			trimmed_data = data.decode('utf-8').rstrip('\r\n')
		self.headers = re.split(delimiter, trimmed_header)
		self.data_row_fields = re.split(delimiter, trimmed_data)
		
		length_check(self.headers, self.data_row_fields)
		
	def get_value(self, desired_header):
		get_spreadsheet_value(self.headers, self.data_row_fields, desired_header)
		
	def spreadsheet_row_to_obj(self):
		x = types.SimpleNamespace()
		for field, value in zip(self.headers, self.data_row_fields):
			setattr(x, field, value)
		return x

def length_check(headers, fields):
	if len(fields) != len (headers):
		raise ValueError(f'mismatch between number of header fields {len(headers)} and number of data fields {len(fields)}. Avoid using tabs and newlines in text fields. Data row is: {fields}')

# simple parsing of a spreadsheet file into a single header row and the data rows that follow
def spreadsheet_headers_and_data_rows(spreadsheet_file):
	s = spreadsheet_file.read()
	try: # for web file upload
		s = s.decode("utf-8")
	except: # direct file
		pass
	lines = s.splitlines()
	header = lines[0]
	data_rows = lines[1:]
	
	headers = header.split(DELIMITER)
	for data_row in data_rows:
		fields = data_row.split(DELIMITER)
		length_check(headers, fields)
	
	return headers, data_rows
	
def spreadsheet_headers_and_data_row_fields(spreadsheet_file):
	headers, data_rows = spreadsheet_headers_and_data_rows(spreadsheet_file)
	data_row_fields = [data_row.split(DELIMITER) for data_row in data_rows]
	return headers, data_row_fields

def get_spreadsheet_value(headers, data_row_fields, desired_header):
	length_check(headers, data_row_fields)
	try:
		index = headers.index(desired_header)
	except ValueError as e:
		if desired_header.endswith(HEADER_READ_ONLY_INDICATOR):
			index = headers.index(desired_header[:-1])
		else:
			raise e
	return data_row_fields[index]

# mark header as read-only
def spreadsheet_header_read_only(header):
	if header.endswith(HEADER_READ_ONLY_INDICATOR):
		return header
	else:
		return header + HEADER_READ_ONLY_INDICATOR

def spreadsheet_headers_read_only(headers):
	return [spreadsheet_header_read_only(header) for header in headers]
	
# if there is no data, this provides empty field padding
def empty_values(headers):
	return ['' for header in headers]

# to prevent text such as '1-1' from being interpreted by Excel as a date (1 Jan)
def csv_text_escape(s):
	return f'="{s}"'
