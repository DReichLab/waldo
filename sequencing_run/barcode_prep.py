from sequencing_run.ssh_command import ssh_command

# Find the set of barcodes used for a sequencing run 
# Save a file in the run directory as input for the software pipeline
def barcodes_used(sequencing_date_string, sequencing_run_name):
	queryForBarcodes = 'SELECT p5_barcode FROM sequenced_library WHERE sequencing_id="%s" AND length(p5_barcode) > 0 UNION SELECT p7_barcode FROM sequenced_library WHERE sequencing_id="%s" AND length(p7_barcode) > 0;' % (sequencing_run_name, sequencing_run_name)
	
	return _barcodes_used(sequencing_date_string, sequencing_run_name, queryForBarcodes, 'barcodes')

def i5_used(sequencing_date_string, sequencing_run_name):
	queryForBarcodes = 'SELECT p5_index FROM sequenced_library WHERE sequencing_id="%s" AND length(p5_index) > 0;' % (sequencing_run_name)
	
	return _barcodes_used(sequencing_date_string, sequencing_run_name, queryForBarcodes, 'i5')

def i7_used(sequencing_date_string, sequencing_run_name):
	queryForBarcodes = 'SELECT p7_index FROM sequenced_library WHERE sequencing_id="%s" AND length(p7_index) > 0;' % (sequencing_run_name)
	
	return _barcodes_used(sequencing_date_string, sequencing_run_name, queryForBarcodes, 'i7')
	
def _barcodes_used(sequencing_date_string, sequencing_run_name, query, extension):
	host = "mym11@login.rc.hms.harvard.edu"
	command = "mysql devadna -N -e '%s'" % (query)
	ssh_result = ssh_command(host, command, False, True)
	
	barcodeSets = []
	for line in ssh_result.stdout.readlines():
		barcodeSets.append(line.strip().upper() ) # uppercase only
	
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
	barcodeLines = map(lambda barcode: "%s\t%s" % (barcode, barcode), barcodeSetForRun)
	barcodeFileTextOutput = '\n'.join(barcodeLines)
	save_file_with_contents(barcodeFileTextOutput, sequencing_date_string, sequencing_run_name, extension, host)
	#print (barcodeSetForRun)
	return barcodeSetForRun

# put a file in the run directory with the requested contents
def save_file_with_contents(contents, sequencing_date_string, sequencing_run_name, extension, host):
	
	saveFileCommand = "echo '%s' > /n/groups/reich/matt/pipeline/run/%s_%s.%s" % (contents, sequencing_date_string, sequencing_run_name, extension)
	#print (saveFileCommand)
	ssh_command(host, saveFileCommand, False, True)
