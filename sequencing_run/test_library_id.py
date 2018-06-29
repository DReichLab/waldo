from django.test import TestCase

from django.conf import settings

from .library_id import LibraryID

# Create your tests here.

class LibraryIDTest(TestCase):
	def test_valid_lysis(self):
		x = 'S0123.Y1.E2.L3'
		
		lib = LibraryID(x)
		self.assertEqual(123, lib.sample)
		self.assertEqual('', lib.sample_suffix)
		self.assertEqual(1, lib.lysis)
		self.assertEqual(2, lib.extract)
		self.assertEqual(3, lib.library)
		
		self.assertEqual(x, str(lib))
	
	def test_no_extact(self):
		x = 'S0002.L1'
		
		lib = LibraryID(x)
		self.assertEqual(2, lib.sample)
		self.assertEqual('', lib.sample_suffix)
		self.assertEqual(None, lib.lysis)
		self.assertEqual(None, lib.extract)
		self.assertEqual(1, lib.library)
		
		self.assertEqual(x, str(lib))
	
	def test_no_lysis(self):
		x = 'S0123.E1.L2'
		
		lib = LibraryID(x)
		self.assertEqual(123, lib.sample)
		self.assertEqual('', lib.sample_suffix)
		self.assertEqual(None, lib.lysis)
		self.assertEqual(1, lib.extract)
		self.assertEqual(2, lib.library)
		
		self.assertEqual(x, str(lib))
		
	def test_control_with_sample_letter(self):
		x = 'S0123a.Y1.E2.L3'
		
		lib = LibraryID(x)
		self.assertEqual(123, lib.sample)
		self.assertEqual('a', lib.sample_suffix)
		self.assertEqual(1, lib.lysis)
		self.assertEqual(2, lib.extract)
		self.assertEqual(3, lib.library)
		
		self.assertEqual(x, str(lib))
		
	def test_no_sample_at_start1(self):
		x = '0123.Y1.E2.L3'
		with self.assertRaises(ValueError):
			lib = LibraryID(x)
			
	def test_no_sample_at_start2(self):
		x = 'Y1.E2.L3'
		with self.assertRaises(ValueError):
			lib = LibraryID(x)
			
	def test_no_library1(self):
		x = 'S0123.Y1.E2.3'
		with self.assertRaises(ValueError):
			lib = LibraryID(x)
	
	def test_no_library2(self):
		x = 'S0123.Y1.E23'
		with self.assertRaises(ValueError):
			lib = LibraryID(x)
			
	def test_extra_id(self):
		x = 'S0123.Y1.X9.E2.L3'
		with self.assertRaises(ValueError):
			lib = LibraryID(x)
