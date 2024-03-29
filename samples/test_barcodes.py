from django.test import SimpleTestCase

from .models import parse_sample_string, Barcode, Library, reverse_complement
from .layout import *

class BarcodesLayoutTest(SimpleTestCase):
	def test_barcode_total_number(self):
		self.assertEqual(PLATE_WELL_COUNT_HALF, len(BARCODES_BY_POSITION))
		
	def test_barcode_bad_odd_p7_offset(self):
		p7_offset = 1
		self.assertRaises(ValueError, barcodes_for_location, 0, p7_offset)
		
	def test_barcode_position(self):
		self.assertEqual('Q1', barcode_at_position(0))
		self.assertEqual('Q6', barcode_at_position(15))
		self.assertEqual('Q16', barcode_at_position(22))
		self.assertEqual('Q44', barcode_at_position(35))
	
	def test_barcodes_p5_is_p7(self):
		for i in range(PLATE_WELL_COUNT_HALF):
			p5, p7 = barcodes_for_location(i, 0)
			self.assertEqual(p5, p7)
			
	def test_barcodes_p7_basic_zero_offset(self):
		p7_offset = 0
		p5_at_0, p7_at_0 = barcodes_for_location(0, p7_offset)
		p5_at_47, p7_at_48 = barcodes_for_location(PLATE_WELL_COUNT_HALF, p7_offset)
		p5_at_95, p7_at_95 = barcodes_for_location(PLATE_WELL_COUNT - 1, p7_offset)
		
		self.assertEquals(p5_at_0, p5_at_47) # left and right of plate p5 barcodes match
		self.assertEquals(p7_at_0, p7_at_95) # p7 is shifted
		
	# p7 barcode offset checking
	def test_barcodes_p7_offset_7(self):
		p7_offset = 8
		p5, p7 = barcodes_for_location(0, p7_offset)
		self.assertEquals(p7, 'Q19')
		
		# right side of plate is shifted again
		p5, p7 = barcodes_for_location(48, p7_offset)
		self.assertEquals(p7, 'Q4')
			
	# p7 barcodes will always be shifted by one between the left and right sides of a plate
	def test_barcodes_p7_left_right(self):
		for p7_offset in range(0, PLATE_WELL_COUNT_HALF, 2):
			p5 = {}
			p7 = {}
			for i in range(PLATE_WELL_COUNT):
				p5[i], p7[i] = barcodes_for_location(i, p7_offset)
			for i in range(PLATE_WELL_COUNT_HALF):
				self.assertEqual(p5[i], p7[(i - p7_offset) % PLATE_WELL_COUNT_HALF])
				# right side of plate has advanced one position
				right_side_index = i - 1
				if right_side_index < 0:
					right_side_index += PLATE_WELL_COUNT_HALF
				self.assertEqual(p7[i], p7[right_side_index + PLATE_WELL_COUNT_HALF])
				
	def test_source_p7_barcodes(self):
		expected_pairs = {
			'Q1': 'A7',
			'Q11': 'H7',
			'Q38': 'A12',
			'Q48': 'H12',
			'Q26': 'D10',
			'Q28': 'B11'
			}
		for barcode, expected_source in expected_pairs.items():
			self.assertEquals(expected_source, p7_qbarcode_source(barcode))

	def test_indices_A1(self):
		s = 'A1'
		n = reverse_plate_location(s)
		self.assertEquals(0, n)
		starting = 3
		p5, p7 = indices_for_location(n, starting)
		self.assertEquals(starting, p5)
		self.assertEquals(1, p7)
		
	def test_indices_A12(self):
		s = 'A12'
		n = reverse_plate_location(s)
		starting = 3
		p5, p7 = indices_for_location(n, starting)
		self.assertEquals(starting, p5)
		self.assertEquals(12, p7)
		
	def test_indices_E1(self):
		s = 'E1'
		n = reverse_plate_location(s)
		starting = 3
		p5, p7 = indices_for_location(n, starting)
		self.assertEquals(starting+1, p5)
		self.assertEquals(49, p7)
	
	def test_indices_H12(self):
		s = 'H12'
		n = reverse_plate_location(s)
		starting = 3
		p5, p7 = indices_for_location(n, starting)
		self.assertEquals(starting+1, p5)
		self.assertEquals(96, p7)

	def test_single_position_index_and_back(self):
		position = 1
		offset = 1
		i5, i7 = indices_for_location(position, offset)
		self.assertEquals(position, location_from_indices(i5, i7))

	def test_indices_from_location_and_back(self):
		for position in range(0, PLATE_WELL_COUNT):
			for offset in range(1, PLATE_WELL_COUNT//2, 2):
				#print(position, offset)
				i5, i7 = indices_for_location(position, offset)
				self.assertEquals(position, location_from_indices(i5, i7))

	def test_single_position_indices_single_stranded_A1(self):
		expected_row = 'A'
		expected_column = 1
		row, column = plate_location(location_from_indices('1ss', ''))
		self.assertEquals(expected_row, row)
		self.assertEquals(expected_column, column)

	def test_single_position_indices_single_stranded_H12(self):
		expected_row = 'H'
		expected_column = 12
		row, column = plate_location(location_from_indices('96ss', ''))
		self.assertEquals(expected_row, row)
		self.assertEquals(expected_column, column)

	def test_single_position_indices_single_stranded_loop(self):
		for location in range(0, PLATE_WELL_COUNT):
			expected_row, expected_column = plate_location(location)
		row, column = plate_location(location_from_indices(f'{location+1}ss', ''))
		self.assertEquals(expected_row, row)
		self.assertEquals(expected_column, column)

# sequences do not actually matter because barcodes are checked by reference and sequences are enforced unique
class LibraryBarcodeCheckTest(SimpleTestCase):
	def test_library_barcode_match(self):
		barcode1 = Barcode(label='1', sequence='AAAAAAA')
		barcode2 = Barcode(label='2', sequence='TTTTTTT')
		
		l1 = Library(p5_barcode=barcode1, p7_barcode=barcode2)
		l2 = Library(p5_barcode=barcode1, p7_barcode=barcode2)
		self.assertFalse(l1.barcodes_are_distinct(l1))
		self.assertFalse(l1.barcodes_are_distinct(l2))
		self.assertFalse(l2.barcodes_are_distinct(l1))
		self.assertFalse(l2.barcodes_are_distinct(l2))
		
	def test_library_barcode_one_match(self):
		barcode1 = Barcode(label='1', sequence='AAAAAAA')
		barcode2 = Barcode(label='2', sequence='TTTTTTT')
		barcode3 = Barcode(label='3', sequence='GGGGGGG')
		
		l1 = Library(p5_barcode=barcode1, p7_barcode=barcode2)
		l2 = Library(p5_barcode=barcode1, p7_barcode=barcode3)
		self.assertFalse(l1.barcodes_are_distinct(l1))
		self.assertTrue(l1.barcodes_are_distinct(l2))
		self.assertTrue(l2.barcodes_are_distinct(l1))
		self.assertFalse(l2.barcodes_are_distinct(l2))
		
	def test_library_barcode_no_match(self):
		barcode1 = Barcode(label='1', sequence='AAAAAAA')
		barcode2 = Barcode(label='2', sequence='TTTTTTT')
		barcode3 = Barcode(label='3', sequence='GGGGGGG')
		barcode4 = Barcode(label='4', sequence='CCCCCCC')
		
		l1 = Library(p5_barcode=barcode1, p7_barcode=barcode2)
		l2 = Library(p5_barcode=barcode3, p7_barcode=barcode4)
		self.assertFalse(l1.barcodes_are_distinct(l1))
		self.assertTrue(l1.barcodes_are_distinct(l2))
		self.assertTrue(l2.barcodes_are_distinct(l1))
		self.assertFalse(l2.barcodes_are_distinct(l2))

class ReverseComplementTest(SimpleTestCase):
	def test_bad_base(self):
		sequence = 'B'
		self.assertRaises(KeyError, reverse_complement, sequence)

	def test_reverse_complement_self(self):
		sequence = 'ACGT'
		result = reverse_complement(sequence)
		self.assertEquals(sequence, result)

	def test_reverse_complement_index(self):
		sequence = 'CCTGCGA'
		expected = 'TCGCAGG'
		result = reverse_complement(sequence)
		self.assertEquals(expected, result)
		twice = reverse_complement(result)
		self.assertEquals(sequence, twice)
