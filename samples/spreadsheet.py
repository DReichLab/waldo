import re

DELIMITER = '\t'
HEADER_READ_ONLY_INDICATOR = '-'

def length_check(headers, fields):
	if len(fields) != len (headers):
		raise ValueError(f'mismatch between number of header fields {len(headers)} and number of data fields {len(fields)}. Avoid using tabs and newlines in text fields. Data row is: {fields}')

# simple parsing of a spreadsheet file into a single header row and the data rows that follow
def spreadsheet_headers_and_data_rows(spreadsheet_file):
	s = spreadsheet_file.read().decode("utf-8")
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
	index = headers.index(desired_header)
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
