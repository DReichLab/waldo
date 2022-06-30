from django.test import SimpleTestCase
from django.core.exceptions import ValidationError

from .layout import PLATE_ROWS, PLATE_WELL_COUNT, plate_location, reverse_plate_location, PlateDomainError, check_plate_domain, layout_and_content_lists
from .models import TimestampedWellPosition
from .layout import rotated_pair_name
			
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
		
	def rotate_test(self, start_str, expected_str):
		x = TimestampedWellPosition()
		x.set_position(start_str)
		# sanity check that starting position looks correct
		self.assertEquals(start_str, str(x))
		# rotate once then check position
		x.rotate()
		self.assertEquals(expected_str, str(x))
		# rotated twice should now be back at start
		x.rotate()
		self.assertEquals(start_str, str(x)) 
		
	def test_rotate_A1(self):
		self.rotate_test('A1', 'H12')
		
	def test_rotate_H12(self):
		self.rotate_test('H12', 'A1')
		
	def test_rotate_C4(self):
		self.rotate_test('C4', 'F9')
		
	def test_rotate_B3(self):
		self.rotate_test('B3', 'G10')
		
	def test_rotate_D11(self):
		self.rotate_test('D11', 'E2')
		
	def test_rotate_F1(self):
		self.rotate_test('F1', 'C12')

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
		
# Check that the name generated for looking for rotated complements works as expected
class RotatedName(SimpleTestCase):
	def test_Crowd(self):
		name = 'Crowd.21_RE'
		expected = 'Crowd.21U_RE'
		
		rotated_name = rotated_pair_name(name)
		rerotated_name = rotated_pair_name(rotated_name)
		self.assertEquals(name, rerotated_name)
		self.assertEquals(expected, rotated_name)
		
	def test_Crowd_bad_parse(self):
		name = 'Crowd_21_RE'
		rotated_name = rotated_pair_name(name)
		self.assertIsNone(rotated_name)
