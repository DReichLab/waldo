from django.test import TestCase

from django.conf import settings

from .models import ReleasedLibrary

# Create your tests here.

class ReleaseLibrariesTests(TestCase):
	def test_latest_release_library_version(self):
		ReleasedLibrary.objects.create(
			sample=1, 
			extract=1,
			library=1,
			experiment='raw',
			udg='half',
			workflow='test',
			path='testpath',
			capture_name='test_capture',
			version=1
		)
		
		ReleasedLibrary.objects.create(
			sample=1, 
			extract=1,
			library=1,
			experiment='raw',
			udg='half',
			workflow='test',
			path='testpath2',
			capture_name='test_capture',
			version=2
		)
		
		library = ReleasedLibrary.objects.filter(sample=1, extract=1, library=1, experiment='raw', udg='half').latest('version')
		self.assertEqual(library.sample, 1)
		self.assertEqual(library.extract, 1)
		self.assertEqual(library.library, 1)
		self.assertEqual(library.path, 'testpath2')
		self.assertEqual(library.capture_name, 'test_capture')
		self.assertEqual(library.version, 2)
		
	def test_latest_empty(self):
		with self.assertRaises(ReleasedLibrary.DoesNotExist):
			library = ReleasedLibrary.objects.filter(sample=1, extract=1, library=1, experiment='raw', udg='half').latest('version')
