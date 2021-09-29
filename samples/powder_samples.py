from django.db.models import Max

from .models import PowderSample, Sample, SamplePrepQueue, PowderBatch
from .models import LysateBatchLayout

import re

# create a PowderSample and assign Reich Lab Sample Number
def new_reich_lab_powder_sample(sample_prep_entry, powder_batch, user):
	SAMPLE_PREP_LAB = 'Reich Lab'
	sample = Sample.objects.get(queue_id=sample_prep_entry.sample.queue_id)
	# if the corresponding sample does not have Reich Lab sample number, then assign it the next one
	if sample.reich_lab_id is None:
		sample.assign_reich_lab_sample_number()
	try:
		if sample_prep_entry.powder_sample != None:
			powder_sample = sample_prep_entry.powder_sample
		else:
			powder_sample = PowderSample.objects.get(sample=sample, powder_batch=powder_batch)
	except PowderSample.DoesNotExist:
		# count how many powder samples there for this sample
		existing_powder_samples = PowderSample.objects.filter(sample=sample)
		powder_sample_int = len(existing_powder_samples) + 1
		
		powder_sample_id = f'S{sample.reich_lab_id}.P{powder_sample_int}'
		powder_sample = PowderSample.objects.create(sample=sample, powder_batch=powder_batch, powder_sample_id=powder_sample_id)
	powder_sample.sample_prep_protocol=sample_prep_entry.sample_prep_protocol
	powder_sample.sample_prep_lab=SAMPLE_PREP_LAB
	powder_sample.save_user = user
	powder_sample.save()
	
	sample_prep_entry.powder_sample = powder_sample
	sample_prep_entry.save_user = user
	sample_prep_entry.save()

def assign_prep_queue_entries_to_powder_batch(powder_batch, sample_prep_ids, user):
	# first clear powder batch
	to_clear = SamplePrepQueue.objects.filter(powder_batch=powder_batch).exclude(id__in=sample_prep_ids)
	for sample_prep_entry in to_clear:
		sample_prep_entry.powder_batch = None
		if sample_prep_entry.powder_sample != None:
			powder_sample = sample_prep_entry.powder_sample
			powder_sample.powder_batch = None
			powder_sample.save_user = user
			powder_sample.save()
		sample_prep_entry.save()
	# add samples prep queue entries to powder batch
	for sample_prep_entry in SamplePrepQueue.objects.filter(id__in=sample_prep_ids):
		if sample_prep_entry.powder_batch == None:
			sample_prep_entry.powder_batch = powder_batch
			sample_prep_entry.save_user = user
			sample_prep_entry.save()
		if sample_prep_entry.powder_sample != None:
			powder_sample = sample_prep_entry.powder_sample
			powder_sample.powder_batch = powder_batch
			powder_sample.save_user = user
			powder_sample.save()
	# assign reich lab sample number
	# Open is the state where samples can be added. If it is not open, then create the powder sample and assign Reich lab sample number
	if powder_batch.status.description != 'Open':
		for sample_prep_entry in SamplePrepQueue.objects.filter(powder_batch=powder_batch):
			new_reich_lab_powder_sample(sample_prep_entry, powder_batch, user)

# it would be better to reuse form validation
def powder_samples_from_spreadsheet(powder_batch_name, spreadsheet_file, user):
	s = spreadsheet_file.read().decode("utf-8")
	powder_batch = PowderBatch.objects.get(name=powder_batch_name)
	powder_samples = PowderSample.objects.filter(powder_batch=powder_batch)
	lines = s.split('\n')
	header = lines[0]
	headers = re.split('\t|\n', header)
	if headers[0] != 'powder_sample_id':
		raise ValueError('powder_sample_id is not first')
		
	for line in lines[1:]:
		fields = re.split('\t|\n', line)
		powder_sample_id = fields[0]
		if len(powder_sample_id) > 0:
			print(powder_sample_id)
			powder_sample = powder_samples.get(powder_sample_id=powder_sample_id)
			powder_sample.from_spreadsheet_row(headers[1:], fields[1:], user)

def assign_powder_samples_to_lysate_batch(lysate_batch, powder_sample_ids, user):
	# remove powder samples that are not assigned but preserve controls
	to_clear = LysateBatchLayout.objects.filter(lysate_batch=lysate_batch).exclude(powder_sample_id__in=powder_sample_ids).exclude(control_type__isnull=False)
	to_clear.delete()
	# add LysateBatchLayout for powder samples
	for powder_sample_id in powder_sample_ids:
		powder_sample = PowderSample.objects.get(id=powder_sample_id)
		powder_sample_mass_for_extract = powder_sample.powder_for_extract
		
		default_values = {'row': 'A', 'column': 1, 'powder_used_mg': powder_sample_mass_for_extract }
		try: 
			lysate_batch_layout = LysateBatchLayout.objects.get(lysate_batch=lysate_batch, powder_sample=powder_sample)
		except LysateBatchLayout.DoesNotExist:
			lysate_batch_layout = LysateBatchLayout(lysate_batch=lysate_batch, powder_sample=powder_sample)
			# well position is set after all powder samples are added, this is just a placeholder
			# existing entries are unchanged
			lysate_batch_layout.row = 'A'
			lysate_batch_layout.column = 1
		
		lysate_batch_layout.powder_used_mg = powder_sample_mass_for_extract
		lysate_batch_layout.save_user = user
		lysate_batch_layout.save()
		
def ensure_powder_sample_reich_lab_sample_ids(lysate_batch):
	for lysate_batch_layout in lysate_batch.layout:
		powder_sample = lysate_batch_layout.powder_sample
		sample = powder_sample.sample
		sample.assign_reich_lab_sample_number()
