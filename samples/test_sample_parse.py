from django.test import SimpleTestCase

from .models import parse_sample_string
from .models import PLATE_ROWS, PLATE_WELL_COUNT, plate_location, reverse_plate_location

class ParseSampleString(SimpleTestCase):
	def test_basic(self):
		s = 'S0242'
		sample_number, control = parse_sample_string(s)
		self.assertEqual(242, sample_number)
		self.assertEqual('', control)
	
	def test_control_single(self):
		s = 'S31234a'
		sample_number, control = parse_sample_string(s)
		self.assertEqual(31234, sample_number)
		self.assertEqual('a', control)
	
	def test_control_long(self):
		s = 'S31234ab'
		sample_number, control = parse_sample_string(s)
		self.assertEqual(31234, sample_number)
		self.assertEqual('ab', control)
	
	def test_control_too_long(self):
		with self.assertRaises(ValueError):
			s = 'S31234abc'
			sample_number, control = parse_sample_string(s)
			
	def test_not_sample(self):
		with self.assertRaises(ValueError):
			s = 'xyz'
			sample_number, control = parse_sample_string(s)
			
class WellPositionArithmetic(SimpleTestCase):
	def test_all_positions(self):
		for row in PLATE_ROWS:
			for column in range(1,13):
				s = row + str(int(column))
				n = reverse_plate_location(s)
				row_expected, column_expected = plate_location(n)
				self.assertEquals(row, row_expected)
				self.assertEquals(column, column_expected)
				
	def test_A1(self):
		s = 'A1'
		n = reverse_plate_location(s)
		self.assertEquals(0, n)
		row, column = plate_location(n)
		self.assertEquals('A', row)
		self.assertEquals(1, column)
		
	def test_H12(self):
		s = 'H12'
		n = reverse_plate_location(s)
		self.assertEquals(95, n)
		row, column = plate_location(n)
		self.assertEquals('H', row)
		self.assertEquals(12, column)
