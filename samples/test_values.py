from django.test import TestCase
from django.test import SimpleTestCase

from samples.models import get_value

import types

# Create your tests here.

class GetValue(SimpleTestCase):
	def test_simple_null_default(self):
		x = None
		self.assertEqual('', get_value(x, 'dummy'))
		
	def test_simple_null_custom_default(self):
		x = None
		default = 'xyz'
		self.assertEqual(default, get_value(x, 'dummy', default=default))
		
	def test_simple_get(self):
		value = 1
		key = 'a'
		x = types.SimpleNamespace()
		setattr(x, key, value)
		self.assertEqual(value, get_value(x, key))
		
	def test_nested_get(self):
		value = 1
		key_a = 'a'
		key_y = 'y'
		x = types.SimpleNamespace()
		y = types.SimpleNamespace()
		setattr(y, key_a, value)
		setattr(x, key_y, y)
		self.assertEqual(value, get_value(x, key_y, key_a))
		
	def test_nested_null(self):
		value = 1
		default = 'xyz'
		key = 'a'
		key2 = 'z'
		x = types.SimpleNamespace()
		setattr(x, key, None)
		self.assertIsNone(get_value(x, key))
		self.assertEqual(default, get_value(x, key, key2, default=default))
