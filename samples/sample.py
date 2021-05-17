from django.conf import settings

import glob

from pathlib import Path

# Zhao stores all photos in the filesystem without database entries. These are implicitly attached samples based on the names. 
def photo_list(reich_lab_sample_number):
	expected_image_folder = Path(f'{settings.MEDIA_ROOT}/S{reich_lab_sample_number/1000:.0f}')

	#print(expected_image_folder)

	image_absolute_paths = glob.glob(str(expected_image_folder / f'*S{reich_lab_sample_number:04d}_*'))
	image_urls = [x.replace(settings.MEDIA_ROOT, '') for x in image_absolute_paths]
	return image_urls
