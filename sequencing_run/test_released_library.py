from django.test import TestCase

from django.conf import settings

from .models import ReleasedLibrary, PositiveControlLibrary, Batch, Capture, SequencingRunID
from .library_id import LibraryID
from .assemble_libraries import latest_library_version
from .report_match_samples import SampleInfo

# Create your tests here.

class ReleaseLibrariesTests(TestCase):
	# simple test of whether of ReleasedLibrary and whether we can retrieve the latest version
	def test_latest_release_library_version(self):
		batch = Batch.objects.create(name='test_batch')
		capture = Capture.objects.create(name='test_capture')
		
		ReleasedLibrary.objects.create(
			sample=1, 
			extract=1,
			library=1,
			experiment='raw',
			udg='half',
			workflow='test',
			path='testpath',
			version=1,
			capture=capture,
			batch=batch
		)
		
		ReleasedLibrary.objects.create(
			sample=1, 
			extract=1,
			library=1,
			experiment='raw',
			udg='half',
			workflow='test',
			path='testpath2',
			version=2,
			capture=capture,
			batch=batch
		)
		
		library = ReleasedLibrary.objects.filter(sample=1, extract=1, library=1, experiment='raw', udg='half').latest('version')
		self.assertEqual(library.sample, 1)
		self.assertEqual(library.extract, 1)
		self.assertEqual(library.library, 1)
		self.assertEqual(library.path, 'testpath2')
		self.assertEqual(library.version, 2)
		
	def test_latest_empty(self):
		with self.assertRaises(ReleasedLibrary.DoesNotExist):
			library = ReleasedLibrary.objects.filter(sample=1, extract=1, library=1, experiment='raw', udg='half').latest('version')
			
	# 
	def test_next_version2_3(self):
		batch = Batch.objects.create(name='test_batch')
		capture = Capture.objects.create(name='test_capture')
		library_id = LibraryID('S9000.E1.L1')
		sample_info = SampleInfo(str(library_id), batch, 'raw', 'half', '', '')
		
		ReleasedLibrary.objects.create(
			sample=library_id.sample, 
			extract=library_id.extract,
			library=library_id.library,
			experiment=sample_info.experiment,
			udg=sample_info.udg,
			workflow='test',
			path='testpath',
			version=1,
			capture=capture,
			batch=batch
		)
		
		self.assertEqual(1, latest_library_version(sample_info))
		
		ReleasedLibrary.objects.create(
			sample=library_id.sample, 
			extract=library_id.extract,
			library=library_id.library,
			experiment=sample_info.experiment,
			udg=sample_info.udg,
			workflow='test',
			path='testpath',
			version=2,
			capture=capture,
			batch=batch
		)
		self.assertEqual(2, latest_library_version(sample_info))
		
	def test_control_library_version(self):
		seqID = SequencingRunID.objects.create(name='Test', order=1)
		batch = Batch.objects.create(name='test_batch')
		capture = Capture.objects.create(name='test_capture')
		sample_info = SampleInfo('Test', batch, 'raw', 'half', '', '')
		
		PositiveControlLibrary.objects.create(
			name=seqID,
			experiment=sample_info.experiment,
			udg=sample_info.udg,
			workflow='test',
			path='testpath',
			version=1,
			capture=capture,
			batch=batch
		)
		self.assertEqual(1,latest_library_version(sample_info))
