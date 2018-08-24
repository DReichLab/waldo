from django.test import TestCase

from django.conf import settings

from .index_barcode_key import IndexBarcodeKey

class IndexBarcodeKeyTest(TestCase):
	def test_no_barcodes(self):
		i5 = 'AGGTATT'
		i7 = 'GCTTCAG'
		key = IndexBarcodeKey(i5, i7)
		
		self.assertEqual(i5, key.i5)
		self.assertEqual(i7, key.i7)
		self.assertEqual('', key.p5)
		self.assertEqual('', key.p7)
		self.assertEqual('AGGTATT_GCTTCAG__', key.__str__())
		
	def test_37_1_Q18_Q21(self):
		i5 = 'GCCATAG'
		i7 = 'TCGCAGG'
		p5 = 'ACGGTCT:CGTTAGA:GTAACTC:TACCGAG'
		p7 = 'AGTCACG:CTAGCGT:GACTGTA:TCGATAC'
		
		key = IndexBarcodeKey(i5, i7, p5, p7)
		
		self.assertEqual(i5, key.i5)
		self.assertEqual(i7, key.i7)
		self.assertEqual(p5, key.p5)
		self.assertEqual(p7, key.p7)
		self.assertEqual('GCCATAG_TCGCAGG_ACGGTCT:CGTTAGA:GTAACTC:TACCGAG_AGTCACG:CTAGCGT:GACTGTA:TCGATAC', key.__str__())
		
		index_only_key = IndexBarcodeKey(i5, i7)
		self.assertFalse(key.maps_to(index_only_key))
		self.assertFalse(index_only_key.maps_to(key))
		
	def test_positive_control(self):
		i5 = 'AGGTATT'
		i7 = 'GCTTCAG'
		
		p5 = 'GGTATCG:TTACAGT:AACGCTA:CCGTGAC'
		p7 = p5
		key_from_data = IndexBarcodeKey(i5, i7, p5, p7)
		
		p5_sheet = 'TTACAGT'
		p7_sheet = 'CCGTGAC'
		key_from_sheet = IndexBarcodeKey(i5, i7, p5_sheet, p7_sheet)
		
		self.assertTrue(key_from_sheet.maps_to(key_from_data))
		self.assertFalse(key_from_data.maps_to(key_from_sheet))
		
	def test_from_string_without_barcodes(self):
		i5 = 'AGGTATT'
		i7 = 'GCTTCAG'
		key = IndexBarcodeKey(i5, i7)
		
		expected_key_string = 'AGGTATT_GCTTCAG__'
		self.assertEqual(expected_key_string, key.__str__())
		key_derived_from_string = IndexBarcodeKey.from_string(key.__str__())
		self.assertEqual(expected_key_string, key_derived_from_string.__str__())

	def test_from_string_with_barcodes(self):
		i5 = 'GCCATAG'
		i7 = 'TCGCAGG'
		p5 = 'ACGGTCT:CGTTAGA:GTAACTC:TACCGAG'
		p7 = 'AGTCACG:CTAGCGT:GACTGTA:TCGATAC'
		
		key = IndexBarcodeKey(i5, i7, p5, p7)
		expected_key_string = 'GCCATAG_TCGCAGG_ACGGTCT:CGTTAGA:GTAACTC:TACCGAG_AGTCACG:CTAGCGT:GACTGTA:TCGATAC'
		self.assertEqual(expected_key_string, key.__str__())
		key_derived_from_string = IndexBarcodeKey.from_string(key.__str__())
		self.assertEqual(expected_key_string, key_derived_from_string.__str__())
