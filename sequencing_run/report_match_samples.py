# Adjust a screening report based on a new sample sheet
# Inputs:
# 1. finished screening report
# 2. sample sheet mapping index-barcodes to library IDs (sample, extract, library) and plate IDs (capture names)
# Output: 
# 1. screening report with results remapped to library IDs and capture names
import sys

# create dictionaries from sample sheet that map index-barcodes to library IDs (S1.E1.L1) and plate IDs(Sugarplum)
# lookup is based on column headers
def readSampleSheet(sample_sheet_filename):
	libraryIDs = {}
	plateIDs = {}
	
	with open(sample_sheet_filename) as f:
		line = f.readline()
		headers = line.split('\t')
		
		libraryID_index = headers.index('Sample_Name')
		i5_index = headers.index('Index2')
		i7_index = headers.index('Index')
		p5_barcode = headers.index('P5_barcode')
		p7_barcode = headers.index('P7_barcode')
		plateID_index = headers.index('Capture_Name')
		
		for line in f:
			fields = line.split('\t')
			key = '{}_{}_{}_{}'.format(fields[i5_index], fields[i7_index], fields[p5_barcode], fields[p7_barcode])
			libraryIDs[key] = fields[libraryID_index]
			plateIDs[key] = fields[plateID_index]
	
	return libraryIDs, plateIDs

# retrieve information from a dictionary using an index-barcode key_index and its subsets
# for barcodes with ':' delimiting multiple barcode sequences, all subset combinations will also be checked
# the successful lookup key is returned as the sampleSheetID
def getInfo(sampleID, keyMapping):
	info = keyMapping.get(sampleID, '')
	sampleSheetID = ''
	if info != '':
		sampleSheetID = sampleID
	else:
		i5, i7, p5_set, p7_set = sampleID.split('_')
		for p5 in p5_set.split(':'):
			for p7 in p7_set.split(':'):
				trialSampleID = '{}_{}_{}_{}'.format(i5, i7, p5, p7)
				trialInfo = keyMapping.get(trialSampleID, '')
				
				if info == '':
					if trialInfo != '':
						info = trialInfo
						sampleSheetID = trialSampleID
				# if there is more than one info that matches, we have a nonprogramming problem
				elif trialInfo != '':
					info = 'MULTIPLE'
					sampleSheetID = 'MULTIPLE'
	return sampleSheetID, info

# return an array of report lines, with libraryID and plateID fields adjusted according to the arguments,
# which are derived from a sample sheet
def relabelSampleLines(report_filename, libraryIDs, plateIDs):
	sampleLines = []
	with open(report_filename) as f:
		line = f.readline().rstrip('\n')
		sampleLines.append(line) # number of reads
		line = f.readline().rstrip('\n')
		sampleLines.append(line) # header
		headers = line.split('\t')
		key_index = headers.index('Index-Barcode Key')
		sample_sheet_key_index = headers.index('sample_sheet_key')
		libraryID_index = headers.index('library_id')
		plateID_index = headers.index('plate_id')
		
		for line in f:
			fields = line.rstrip('\n').split('\t')
			key = fields[key_index]
			sampleSheetID1, fields[libraryID_index] = getInfo(key, libraryIDs)
			sampleSheetID2, fields[plateID_index] = getInfo(key, plateIDs)
			if sampleSheetID1 != sampleSheetID2:
				raise ValueError('sample sheet ID mismatch {} != {}'.format(sampleSheetID1, sampleSheetID2))
			fields[sample_sheet_key_index] = sampleSheetID1
			sampleLine = '\t'.join(fields)
			sampleLines.append(sampleLine)
	return sampleLines
			
if __name__ == "__main__":
	report_filename = sys.argv[1]
	sample_sheet_filename = sys.argv[2]
	
	libraryIDs, plateIDs = readSampleSheet(sample_sheet_filename)

	sampleLines = relabelSampleLines(report_filename, libraryIDs, plateIDs)
	for sample in sampleLines:
		print(sample)
