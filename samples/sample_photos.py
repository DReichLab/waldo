from django.conf import settings

import glob

from pathlib import Path

# Zhao stores all photos in the filesystem without database entries. These are implicitly attached samples based on the names. 
# file name examples:
# 130423_S0129_After_v2.jpg
# S10744_After_V1.jpg (this is the template we use here for saving new files)
# S10855_Post_V1.JPG

# the subfolder for images depends on the thousands
def photo_folder(reich_lab_sample_number):
	return Path(f'{settings.MEDIA_ROOT}/S{reich_lab_sample_number//1000:d}')

# List all of the photos for a sample
def photo_list(reich_lab_sample_number):
	expected_image_folder = photo_folder(reich_lab_sample_number)

	image_absolute_paths = glob.glob(str(expected_image_folder / f'*S{reich_lab_sample_number:04d}_*'))
	image_urls = [x.replace(settings.MEDIA_ROOT, '') for x in image_absolute_paths]
	return image_urls
	
def num_sample_photos(reich_lab_sample_number):
	return len(photo_list(reich_lab_sample_number))

# Save a photo with the next version
# labels are from the web form and are not checked here
def save_sample_photo(uploaded_photo, reich_lab_sample_number, label):
	folder = photo_folder(reich_lab_sample_number)
	if not folder.exists():
		folder.mkdir()
	try: # in case we are not the owner, don't fail trying to change permissions
		folder.chmod(0o775)
	except:
		pass
	extension = Path(uploaded_photo.name).suffix.lower()
	
	version = 1
	while version == 1 or photo_path.exists():
		photo_filename = f'S{reich_lab_sample_number:04d}_{label}_V{version}{extension}'
		photo_path = folder / photo_filename
		version += 1
	
	with open(photo_path, 'wb') as destination:
		for chunk in uploaded_photo.chunks():
			destination.write(chunk)
	Path(photo_path).chmod(0o664)

# photo_relative_path is relative to settings.MEDIA_ROOT
def delete_photo(photo_relative_path, reich_lab_sample_number):
	photo = Path(f'{settings.MEDIA_ROOT}/{photo_relative_path}')
	# check that the reich lab sample number is in the filename
	if str(reich_lab_sample_number) in photo.stem:
		photo.unlink()
	else:
		raise ValueError('S{reich_lab_sample_number} is not in {photo_relative_path} file name')
	
