def index_barcode_key_to_fields(index_barcode_key):
	fields = index_barcode_key.split('_')
	i5 = fields[0]
	i7 = fields[1]
	# if this key is from a filename, preemptively replace '-' to standardize on ':' barcode separators
	p5 = fields[2].replace('-', ':')
	p7 = fields[3].replace('-', ':')
	
	return i5, i7, p5, p7

class SampleSheetEntry:
	# integer IDs
	#sample
	#extract
	#library
	
	# sequencing indices and barcodes
	#i5_index
	#i7_index
	#p5_barcode
	#p7_barcode
	
	def __init__(self):
		self.sample = 0
		self.extract = 0
		self.library = 0
	
	def getSampleExtractLibraryID(self):
		sampleID = 'S{:d}.E{:d}.L{:d}'.format(self.sample, self.extract, self.library)
		return sampleID
	
	def getI5Index(self):
		return self.i5_index
	
	def getI7Index(self):
		return self.i7_index
	
	def getP5Barcode(self):
		return self.p5_barcode
	
	def getP7Barcode(self):
		return self.p7_barcode
	

class SampleSheet:
	samples = {}
	
	def read_from_file():
		pass
		
