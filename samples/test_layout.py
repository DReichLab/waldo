from django.test import SimpleTestCase

from .layout import PLATE_ROWS, PLATE_WELL_COUNT, plate_location, reverse_plate_location, PlateDomainError, check_plate_domain
			
class WellPositionArithmetic(SimpleTestCase):
	def test_check_plate_domain_good(self):
		for i in range(PLATE_WELL_COUNT):
			check_plate_domain(i)
			
	def test_check_plate_domain_out_of_range(self):
		self.assertRaises(PlateDomainError, check_plate_domain, -1)
		self.assertRaises(PlateDomainError, check_plate_domain, PLATE_WELL_COUNT)
	
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
		
	def out_of_domain_position(self):
		self.assertRaises(PlateDomainError, plate_location, -1)
