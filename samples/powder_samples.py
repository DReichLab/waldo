from django.db.models import Max

from .models import PowderSample, Sample

import re

# create a PowderSample and assign Reich Lab Sample Number
def new_reich_lab_powder_sample(sample_queue_id, powder_batch, sample_prep_entry):
	SAMPLE_PREP_LAB = 'Reich Lab'
	sample = Sample.objects.get(queue_id=sample_queue_id)
	# if the corresponding sample does not have Reich Lab sample number, then assign it the next one
	if sample.reich_lab_id is None:
		max_sample_number = Sample.objects.all().aggregate(Max('reich_lab_id'))['reich_lab_id__max']
		next_sample_number = max_sample_number + 1
		sample.reich_lab_id = next_sample_number
		sample.save()
		return max_sample_number
	try:
		powder_sample = PowderSample.objects.get(sample=sample, powder_batch=powder_batch)
	except PowderSample.DoesNotExist:
		# count how many powder samples there for this sample
		existing_powder_samples = PowderSample.objects.filter(sample=sample)
		powder_sample_int = len(existing_powder_samples) + 1
		# TODO powder_sample_int should not be converted into a string. Model needs to be changed.
		powder_sample_id = f'S{sample.reich_lab_id}.P{powder_sample_int}'
		powder_sample = PowderSample.objects.create(sample=sample, powder_batch=powder_batch, powder_sample_id=powder_sample_id)
	powder_sample.sample_prep_protocol=sample_prep_entry.sample_prep_protocol
	powder_sample.sample_prep_lab=SAMPLE_PREP_LAB
	powder_sample.save()

# TODO
# update 
def powder_samples_from_spreadsheet(spreadsheet_file):
	with open(spreadsheet_file) as f:
		header = f.readline()
		headers = re.split('\t|\n', header)
