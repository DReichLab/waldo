# Adjust a screening report based on a new sample sheet
# Inputs:
# 1. finished screening report
# 2. sample sheet mapping index-barcodes to library IDs (sample, extract, library) and plate IDs (capture names)
# Output: 
# 1. screening report with results remapped to library IDs and capture names
import sys

class SampleInfo:
	def __init__(self, libraryID, plateID, experiment, udg):
		self.libraryID = libraryID
		self.plateID = plateID
		self.experiment = experiment
		self.udg = udg
		
	def is_empty(self):
		return (self.libraryID == '' and self.plateID == '' and self.experiment == '' and self.udg == '')

# create dictionaries from sample sheet that map index-barcodes to library IDs (S1.E1.L1) and plate IDs(Sugarplum)
# lookup is based on column headers
def readSampleSheet(sample_sheet_filename):	
	try:
		return readSampleSheet_encoding(sample_sheet_filename, 'utf-8')
	except:
		return readSampleSheet_encoding(sample_sheet_filename, 'windows-1252')

def readSampleSheet_encoding(sample_sheet_filename, encoding):
	with open(sample_sheet_filename, encoding=encoding) as f:
		sample_sheet_contents_array = f.readlines()
		return readSampleSheet_array(sample_sheet_contents_array)

def readSampleSheet_array(sample_sheet_contents_array):
	samples_parameters = {}
	
	header_line = sample_sheet_contents_array[0]
	headers = header_line.split('\t')
	libraryID_index = headers.index('Sample_Name')
	i5_index = headers.index('Index2')
	i7_index = headers.index('Index')
	p5_barcode = headers.index('P5_barcode')
	p7_barcode = headers.index('P7_barcode')
	experiment_index = headers.index('Experiment')
	plateID_index = headers.index('Capture_Name')
	udg_index = headers.index('UDG_treatment')
	
	data_lines = sample_sheet_contents_array[1:]
	for line in data_lines:
		fields = line.split('\t')
		key = '{}_{}_{}_{}'.format(fields[i5_index], fields[i7_index], fields[p5_barcode], fields[p7_barcode])
		samples_parameters[key] = SampleInfo(fields[libraryID_index], fields[plateID_index], fields[experiment_index], fields[udg_index])
		
	return samples_parameters

# retrieve information from a dictionary using an index-barcode key_index and its subsets
# for barcodes with ':' delimiting multiple barcode sequences, all subset combinations will also be checked
# the successful lookup key is returned as the sampleSheetID
def getInfo(sampleID, keyMapping):
	info = keyMapping.get(sampleID, SampleInfo('', '', '', ''))
	sampleSheetID = ''
	if info != '':
		sampleSheetID = sampleID
	else:
		i5, i7, p5_set, p7_set = sampleID.split('_')
		for p5 in p5_set.split(':'):
			for p7 in p7_set.split(':'):
				trialSampleID = '{}_{}_{}_{}'.format(i5, i7, p5, p7)
				trialInfo = keyMapping.get(trialSampleID, SampleInfo('', '', '', ''))
				
				if info.is_empty():
					if not trialInfo.is_empty():
						info = trialInfo
						sampleSheetID = trialSampleID
				# if there is more than one info that matches, we have a nonprogramming problem
				elif not trialInfo.is_empty():
					info = SampleInfo('MULTIPLE', 'MULTIPLE', 'MULTIPLE', 'MULTIPLE')
					sampleSheetID = 'MULTIPLE'
	return sampleSheetID, info

# return an array of report lines, with libraryID and plateID fields adjusted according to the arguments,
# which are derived from a sample sheet
def relabelSampleLines(report_filename, samples_parameters):
	with open(report_filename) as f:
		sample_lines_input = f.readlines()
		return relabelSampleLines_array(sample_lines_input, samples_parameters)
		
	
def relabelSampleLines_array(sample_lines_input, samples_parameters):
	sampleLines = []
	
	line = sample_lines_input[0].rstrip('\n')
	sampleLines.append(line) # number of reads
	line = sample_lines_input[1].rstrip('\n')
	sampleLines.append(line) # header
	headers = line.split('\t')
	key_index = headers.index('Index-Barcode Key')
	sample_sheet_key_index = headers.index('sample_sheet_key')
	libraryID_index = headers.index('library_id')
	plateID_index = headers.index('plate_id')
	experiment_index= headers.index('experiment')
	
	for line in sample_lines_input[2:]:
		fields = line.rstrip('\n').split('\t')
		key = fields[key_index]
		sampleSheetID, single_sample_parameters = getInfo(key, samples_parameters)
		fields[libraryID_index] = single_sample_parameters.libraryID
		fields[plateID_index] = single_sample_parameters.plateID
		fields[experiment_index] = single_sample_parameters.experiment
		# udg field is not currently present in report to rewrite
		
		fields[sample_sheet_key_index] = sampleSheetID
		sampleLine = '\t'.join(fields)
		sampleLines.append(sampleLine)
	return sampleLines
			
if __name__ == "__main__":
	report_filename = sys.argv[1]
	sample_sheet_filename = sys.argv[2]
	
	samples_parameters = readSampleSheet(sample_sheet_filename)

	sampleLines = relabelSampleLines(report_filename, samples_parameters)
	for sample in sampleLines:
		print(sample)
