from django.test import SimpleTestCase

from .models import parse_sample_string

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

	def test_library_string_control(self):
		s = 'S12345a.Y1.E1.L1'
		sample_number, control = parse_sample_string(s, False)
		self.assertEqual(12345, sample_number)
		self.assertEqual('a', control)

	def test_library_string(self):
		s = 'S54321.Y1.E1.L1'
		sample_number, control = parse_sample_string(s, False)
		self.assertEqual(54321, sample_number)
		self.assertEqual('', control)

	def test_library_string_full_fail(self):
		s = 'S12345a.Y1.E1.L1'
		with self.assertRaises(ValueError):
			sample_number, control = parse_sample_string(s, True)
