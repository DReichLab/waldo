from django.test import SimpleTestCase
from django.core.exceptions import ValidationError

from .layout import PLATE_ROWS, PLATE_WELL_COUNT, plate_location, reverse_plate_location, PlateDomainError, check_plate_domain, layout_and_content_lists
from .models import TimestampedWellPosition
			
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
		
	def test_out_of_domain_position(self):
		self.assertRaises(PlateDomainError, plate_location, -1)

	def test_layout_and_content_lists(self):
		checkbox_values = ['1_100', '2_200', '_300', '_400']
		layout_ids, new_content_ids = layout_and_content_lists(checkbox_values)
		self.assertEquals(1, layout_ids[0])
		self.assertEquals(2, layout_ids[1])
		self.assertEquals(300, new_content_ids[0])
		self.assertEquals(400, new_content_ids[1])

class WellPositionValidation(SimpleTestCase):
	def test_A1(self):
		x = TimestampedWellPosition()
		x.set_position('A1')
		x.clean()
		
	def test_row_only(self):
		x = TimestampedWellPosition()
		x.row = 'A'
		with self.assertRaises(ValidationError):
			x.clean()
			
	def test_column_only(self):
		x = TimestampedWellPosition()
		x.column = '2'
		with self.assertRaises(ValidationError):
			x.clean()
			
	def test_no_position(self):
		x = TimestampedWellPosition()
		x.clean()
