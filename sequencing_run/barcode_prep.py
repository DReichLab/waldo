from ssh_command import ssh_command
from barcode_map import barcode_to_label, barcode_to_full_barcode_set

def barcodes_used(sequencing_run_name):
	host = "mym11@login.rc.hms.harvard.edu"
	queryForBarcodes = 'SELECT p5_barcode FROM sequenced_library WHERE sequencing_id="%s" AND length(p5_barcode) > 0 UNION SELECT p7_barcode FROM sequenced_library WHERE sequencing_id="%s" AND length(p7_barcode) > 0;' % (sequencing_run_name, sequencing_run_name)
	command = "mysql devadna -N -e '%s'" % (queryForBarcodes)
	ssh_result = ssh_command(host, command, False, True)
	
	barcodeSet = {}
	for line in ssh_result.stdout.readlines():
		barcode = line.strip().upper() # uppercase only
		barcodeSet[barcode] = 0
	
	# on first pass, populate sets with more than one barcode
	barcodeMapForRun = {}
	for barcode in barcodeSet:
		if ':' in barcode:
			label = barcode_to_label(barcode)
			barcodeMapForRun[barcode] = label
	# on second pass, add singleton barcodes
	for barcode in barcodeSet:
		if ':' not in barcode:
			fullBarcodeSet = barcode_to_full_barcode_set(barcode)
			if fullBarcodeSet not in barcodeMapForRun:
				barcodeMapForRun[barcode] = barcode
	
	for barcode in barcodeMapForRun:
		print("%s\t%s" % (barcode, barcodeMapForRun[barcode]) )
