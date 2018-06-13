from django.test import TestCase

from django.conf import settings

from .models import ReleasedLibrary, Batch, Capture

# Create your tests here.

class ReleaseLibrariesTests(TestCase):
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
