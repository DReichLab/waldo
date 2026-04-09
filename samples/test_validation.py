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
		
class AlphanumericPlusValidation(SimpleTestCase):
	def test_letters(self):
		validate_alphanumeric_plus('abcd')

	def test_alphanumeric(self):
		validate_alphanumeric_plus('I12345')

	def test_dash(self):
		validate_alphanumeric_plus('I12345-2')

	def test_underscore(self):
		validate_alphanumeric_plus('I12345_2')

	def test_dot(self):
		validate_alphanumeric_plus('I12345.2')
		
	def test_digits(self):
		validate_alphanumeric_plus('0987')

	def test_space(self):
		with self.assertRaises(ValidationError):
			validate_alphanumeric_plus('ab cd')

	def test_bad_punctuation_dollar(self):
		with self.assertRaises(ValidationError):
			validate_alphanumeric_plus('$')

	def test_bad_punctuation_caret(self):
		with self.assertRaises(ValidationError):
			validate_alphanumeric_plus('^')

	def test_bad_punctuation_exclamation(self):
		with self.assertRaises(ValidationError):
			validate_alphanumeric_plus('!')

	def test_bad_punctuation_star(self):
		with self.assertRaises(ValidationError):
			validate_alphanumeric_plus('*')

	def test_bad_punctuation_backslash(self):
		with self.assertRaises(ValidationError):
			validate_alphanumeric_plus('\\')
