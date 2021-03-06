from .ssh_command import ssh_command, save_file_with_contents
from django.conf import settings

# Find the set of barcodes used for a sequencing run
# Query the database for:
# 1. p5 barcodes in sample sheet
# 2. p7 barcodes in sample sheet
# 3. standard Reich Lab Q barcodes from barcode table (expected to be static)
# Save a file in the run directory as input for the software pipeline
def barcodes_set(sequencing_date_string, combined_sequencing_run_name, sequencing_run_names, explicit_additions = []):
	where_clauses = " OR ".join(['sequencing_id="{}"'.format(name) for name in sequencing_run_names])
	queryForBarcodes = 'SELECT UPPER(p5_barcode) FROM sequenced_library WHERE ({0}) AND length(p5_barcode) > 0 UNION SELECT UPPER(p7_barcode) FROM sequenced_library WHERE ({0}) AND length(p7_barcode) > 0 UNION SELECT barcode FROM barcode WHERE barcode_id LIKE "Q%";'.format(where_clauses)
	
	return _barcodes_set(sequencing_date_string, combined_sequencing_run_name, queryForBarcodes, 'barcodes', explicit_additions)


# i5 indices from sample sheet plus standard Reich Lab i5 indices (1-48) and the shotgun indices (49-53)
# eliminate '..' entries by requiring length > 3
# new_p5_index is 8 base-pair single stranded indices
def i5_set(sequencing_date_string, combined_sequencing_run_name, sequencing_run_names, explicit_additions = []):
	where_clauses = " OR ".join(['sequencing_id="{}"'.format(name) for name in sequencing_run_names])
	queryForBarcodes = 'SELECT UPPER(p5_index) FROM sequenced_library WHERE ({}) AND length(p5_index) > 3 UNION SELECT UPPER(sequence) FROM p5_index WHERE p5_index_key BETWEEN 1 AND 53 UNION SELECT UPPER(p5_index_seq) FROM new_p5_index;'.format(where_clauses)
	
	return _barcodes_set(sequencing_date_string, combined_sequencing_run_name, queryForBarcodes, 'i5', explicit_additions)

# i7 indices from sample sheet plus standard Reich Lab i7 indices (1-96)
# eliminate '..' entries by requiring length > 3
# new_p7_index is 8 base-pair single stranded indices
def i7_set(sequencing_date_string, combined_sequencing_run_name, sequencing_run_names, explicit_additions = []):
	where_clauses = " OR ".join(['sequencing_id="{}"'.format(name) for name in sequencing_run_names])
	queryForBarcodes = 'SELECT UPPER(p7_index) FROM sequenced_library WHERE ({}) AND length(p7_index) > 3 UNION SELECT UPPER(sequence) FROM p7_index WHERE p7_index_key BETWEEN 1 AND 96 UNION SELECT UPPER(p7_index_seq) FROM new_p7_index;'.format(where_clauses)
	
	return _barcodes_set(sequencing_date_string, combined_sequencing_run_name, queryForBarcodes, 'i7', explicit_additions)

# run a database query with the 
def _barcodes_set(sequencing_date_string, combined_sequencing_run_name, query, extension, explicit_additions = []):
	host = settings.COMMAND_HOST
	command = "mysql devadna -N -e '{}'".format(query)
	ssh_result = ssh_command(host, command, False, True)
	
	barcodeSets = []
	for line in ssh_result.stdout.readlines():
		barcodeSets.append(line.strip().upper() ) # uppercase only
	# add explicit additions if not already present
	for barcode in explicit_additions:
		if barcode not in barcodeSets:
			barcodeSets.append(barcode)
	
	barcodeSetForRun = set()
	usedBarcodes = set()
	# on first pass, populate sets with more than one barcode
	for barcodeSet in barcodeSets:
		if ':' in barcodeSet:
			barcodeSetForRun.add(barcodeSet)
			# each individual barcode will be considered as this set
			individualBarcodes = barcodeSet.split(':')
			for individualBarcode in individualBarcodes:
				usedBarcodes.add(individualBarcode)
				
	# on second pass, add singleton barcodes
	for barcode in barcodeSets:
		if (':' not in barcode) and (barcode not in usedBarcodes) and (barcode not in barcodeSetForRun):
			barcodeSetForRun.add(barcode)
	
	# print the barcode twice because the format is [barcode label]
	barcodeLines = ["{0}\t{0}".format(barcode) for barcode in barcodeSetForRun]
	barcodeFileTextOutput = '\n'.join(barcodeLines)
	save_file_with_contents(barcodeFileTextOutput, sequencing_date_string, combined_sequencing_run_name, extension, host)
	#print (barcodeSetForRun)
	return barcodeSetForRun
