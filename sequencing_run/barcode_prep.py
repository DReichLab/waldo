from django.conf import settings
from django.db.models import Q
from samples.models import Barcode, P5_Index, P7_Index, SequencingRun

# Find the set of barcodes used for a sequencing run
# Query the database for:
# 1. p5 barcodes in sample sheet
# 2. p7 barcodes in sample sheet
# 3. standard Reich Lab Q barcodes from barcode table (expected to be static)
# Save a file in the run directory as input for the software pipeline
def barcodes_set(sequencing_date_string, combined_sequencing_run_name, sequencing_run_names, explicit_additions = []):
	barcodes = []
	for sequencing_run_name in sequencing_run_names:
		sequencing_run = SequencingRun.objects.get(name=sequencing_run_name)
		barcodes += sequencing_run.barcodes()
	
	return _barcodes_set(sequencing_date_string, combined_sequencing_run_name, barcodes, 'barcodes', explicit_additions)

# i5 indices from sample sheet plus standard Reich Lab i5 indices (1-48) and the shotgun indices (49-53)
# new_p5_index is 8 base-pair single stranded indices
def i5_set(sequencing_date_string, combined_sequencing_run_name, sequencing_run_names, explicit_additions = []):
	i5 = []
	for sequencing_run_name in sequencing_run_names:
		sequencing_run = SequencingRun.objects.get(name=sequencing_run_name)
		i5 += sequencing_run.i5_indices()
	
	return _barcodes_set(sequencing_date_string, combined_sequencing_run_name, i5, 'i5', explicit_additions)

# i7 indices from sample sheet plus standard Reich Lab i7 indices (1-96)
# new_p7_index is 8 base-pair single stranded indices
def i7_set(sequencing_date_string, combined_sequencing_run_name, sequencing_run_names, explicit_additions = []):
	i7 = []
	for sequencing_run_name in sequencing_run_names:
		sequencing_run = SequencingRun.objects.get(name=sequencing_run_name)
		i7 += sequencing_run.i7_indices()
	
	return _barcodes_set(sequencing_date_string, combined_sequencing_run_name, i7, 'i7', explicit_additions)

# put a file in the run directory with the requested contents
def save_file_with_contents(contents, sequencing_date_string, sequencing_run_name, extension):
	filename = f"{sequencing_date_string}_{sequencing_run_name}.{extension}"
	directory = f"{settings.RUN_FILES_DIRECTORY}/{sequencing_date_string}_{sequencing_run_name}"
	with open(f'{directory}/{filename}', 'w') as f:
		f.write(contents)

# run a database query with the 
def _barcodes_set(sequencing_date_string, combined_sequencing_run_name, sequences_list, extension, explicit_additions = []):
	barcodeSets = []
	for line in sequences_list:
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
	save_file_with_contents(barcodeFileTextOutput, sequencing_date_string, combined_sequencing_run_name, extension)
	#print (barcodeSetForRun)
	return barcodeSetForRun
