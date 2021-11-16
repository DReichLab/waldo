from django.test import SimpleTestCase
from django.core.exceptions import ValidationError

from .validation import *

class WhitespaceValidation(SimpleTestCase):
	def test_nowhitespace(self):
		s = 'abc'
		validate_no_whitespace(s)
	
	def test_space(self):
		with self.assertRaises(ValidationError):
			s = ' '
			validate_no_whitespace(s)
			
	def test_space2(self):
		with self.assertRaises(ValidationError):
			s = 'abc def'
			validate_no_whitespace(s)
			
	def test_tab(self):
		with self.assertRaises(ValidationError):
			s = '\t'
			validate_no_whitespace(s)

class UnderscoreValidation(SimpleTestCase):
	def test_letters(self):
		s = 'abc'
		validate_no_underscore(s)
		
	def test_underscore(self):
		with self.assertRaises(ValidationError):
			s = 'ab_c'
			validate_no_underscore(s)
		
