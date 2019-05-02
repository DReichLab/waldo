from django.test import TestCase

from django.conf import settings

from sequencing_run.management.commands import load_demultiplexed

class FlowcellIDTest(TestCase):
	def test_parse_flowcell_id_single(self):
		flowcell_text_input = ['PM:NS500217     PU:HWCHLBGX3.488.1']
		results = load_demultiplexed.Command.read_flowcell_text_ids_from_file_contents(None, flowcell_text_input, False)
		self.assertEqual(1, len(results))
		self.assertEqual('HWCHLBGX3', results[0])
		
	def test_parse_flowcell_id_multiple(self):
		flowcell_text_input = [
			'PM:NS500217     PU:HWCHLBGX3.488.1',
			'PM:NS500217     PU:HWCHLBGX4.489.1'
			]
		results = load_demultiplexed.Command.read_flowcell_text_ids_from_file_contents(None, flowcell_text_input, False)
		self.assertEqual(2, len(results))
		self.assertEqual('HWCHLBGX3', results[0])
		self.assertEqual('HWCHLBGX4', results[1])
	
	def test_parse_flowcell_id_single_lane(self):
		flowcell_text_input = ['PM:NS500217     PU:HWCHLBGX3.488.1']
		results = load_demultiplexed.Command.read_flowcell_text_ids_from_file_contents(None, flowcell_text_input, True)
		self.assertEqual(1, len(results))
		self.assertEqual('HWCHLBGX3.1', results[0])
		
	def test_parse_flowcell_id_single_multiple(self):
		flowcell_text_input = [
			'PM:NS500217     PU:HWCHLBGX3.488.1',
			'PM:NS500217     PU:HWCHLBGX3.488.2',
			'PM:NS500217     PU:HWCHLBGX4.489.1'
			]
		results = load_demultiplexed.Command.read_flowcell_text_ids_from_file_contents(None, flowcell_text_input, True)
		self.assertEqual(3, len(results))
		self.assertEqual('HWCHLBGX3.1', results[0])
		self.assertEqual('HWCHLBGX3.2', results[1])
		self.assertEqual('HWCHLBGX4.1', results[2])
