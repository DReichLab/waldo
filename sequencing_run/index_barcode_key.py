class IndexBarcodeKey():
	BARCODE_DELIMITER = ':'
	FIELD_DELIMITER = '_'
	
	def __init__(self, i5, i7, p5='', p7=''):
		self.i5 = i5 
		self.i7 = i7
		
		if len(self.i5) != len(self.i7):
			raise ValueError('mismatch in index lengths')
		
		self.p5 = p5 
		self.p7 = p7
		
		if len(self.p5) != len(self.p7):
			raise ValueError('mismatch in barcode lengths')
		for barcode_p5_element in self.p5.split(IndexBarcodeKey.BARCODE_DELIMITER):
			for barcode_p7_element in self.p7.split(IndexBarcodeKey.BARCODE_DELIMITER):
				if len(barcode_p5_element) != len(barcode_p7_element):
					raise ValueError('mismatch in barcode lengths')
				
	def __str__(self):
		return IndexBarcodeKey.FIELD_DELIMITER.join([self.i5, self.i7, self.p5, self.p7])
	
	@classmethod
	def from_string(cls, index_barcode_key_string):
		fields = index_barcode_key_string.split(IndexBarcodeKey.FIELD_DELIMITER)
		return cls(fields[0], fields[1], fields[2], fields[3])
	
	def barcode_subset(barcode_A, barcode_B):
		A = barcode_A.split(IndexBarcodeKey.BARCODE_DELIMITER)
		B = barcode_B.split(IndexBarcodeKey.BARCODE_DELIMITER)
		barcodeLengthA = len(A[0])
		barcodeLengthB = len(B[0])
		if barcodeLengthA != barcodeLengthB:
			return False
		for barcode in A:
			if barcode not in B:
				return False;
		return True;
	
	def maps_to(self, other):
		return (self.i5 == other.i5 and self.i7 == other.i7
			and IndexBarcodeKey.barcode_subset(self.p5, other.p5) and IndexBarcodeKey.barcode_subset(self.p7, other.p7))
