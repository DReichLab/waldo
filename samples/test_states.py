from django.test import SimpleTestCase

from .models import LysateBatch, ExtractionBatch

class LysateBatchStateTest(SimpleTestCase):
	def match_state_and_string(self, state_int, state_name):
		x = LysateBatch()
		x.status = state_int
		self.assertEqual(x.get_status(), state_name)
	
	def test_recall_state_open(self):
		self.match_state_and_string(LysateBatch.OPEN, 'Open')
	
	def test_recall_state_inprogress(self):
		self.match_state_and_string(LysateBatch.IN_PROGRESS, 'In progress')
		
	def test_recall_state_closed(self):
		self.match_state_and_string(LysateBatch.CLOSED, 'Closed')
		
	def test_recall_state_stop(self):
		self.match_state_and_string(LysateBatch.STOP, 'Stop')
		
	def test_nonexistent_state(self):
		x = LysateBatch()
		x.status = -123
		with self.assertRaises(ValueError):
			x.get_status()

class ExtractionBatchStateTest(SimpleTestCase):
	def match_state_and_string(self, state_int, state_name):
		x = ExtractionBatch()
		x.status = state_int
		self.assertEqual(x.get_status(), state_name)
	
	def test_recall_state_open(self):
		self.match_state_and_string(ExtractionBatch.OPEN, 'Open')
		
	def test_recall_state_inprogress(self):
		self.match_state_and_string(ExtractionBatch.IN_PROGRESS, 'In progress')
	
	def test_recall_state_closed(self):
		self.match_state_and_string(ExtractionBatch.CLOSED, 'Closed')
		
	def test_recall_state_stop(self):
		self.match_state_and_string(ExtractionBatch.STOP, 'Stop')
		
	def test_nonexistent_state(self):
		x = ExtractionBatch()
		x.status = -123
		with self.assertRaises(ValueError):
			x.get_status()
