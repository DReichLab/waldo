import re

def length_check(headers, fields):
	if len(fields) != len (headers):
		raise ValueError(f'mismatch between number of header fields {len(headers)} and number of data fields {len(fields)}. Avoid using tabs and newlines in text fields. Data row is: {fields}')

# simple parsing of a spreadsheet file into a single header row and the data rows that follow
def spreadsheet_headers_and_data_rows(spreadsheet_file):
	s = spreadsheet_file.read().decode("utf-8")
	lines = s.splitlines()
	header = lines[0]
	data_rows = lines[1:]
	
	headers = header.split('\t')
	for data_row in data_rows:
		fields = data_row.split('\t')
		length_check(headers, fields)
	
	return headers, data_rows

def get_spreadsheet_value(headers, data_row_fields, desired_header):
	length_check(headers, data_row_fields)
	index = headers.index(desired_header)
	return data_row_fields[index]
