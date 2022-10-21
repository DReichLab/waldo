from django.test import SimpleTestCase

from .models import LysateBatch

class LysateBatchStateTest(SimpleTestCase):
	def test_recall_state_closed(self):
		x = LysateBatch()
		x.status = LysateBatch.CLOSED
		self.assertEqual(x.get_status(), 'Closed')
