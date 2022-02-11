from django.db.models import Max

from .models import PowderSample, Sample, SamplePrepQueue, PowderBatch
from .models import LysateBatchLayout, ExtractionBatchLayout

# create a PowderSample and assign Reich Lab Sample Number
def new_reich_lab_powder_sample(sample_prep_entry, powder_batch, user):
	SAMPLE_PREP_LAB = 'Reich Lab'
	sample = sample_prep_entry.sample
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
	failed_assignments = {}
	# first clear powder batch
	to_clear = SamplePrepQueue.objects.filter(powder_batch=powder_batch).exclude(id__in=sample_prep_ids)
	for sample_prep_entry in to_clear:
		sample_prep_entry.powder_batch = None
		# existing powder sample is destroyed for this sample prep entry
		if sample_prep_entry.powder_sample != None:
			# in models, powder sample is protected if there is a lysate
			# sample prep entry sets reference to null
			sample_prep_entry.powder_sample.delete()
		sample_prep_entry.save(save_user=user)
	# add samples prep queue entries to powder batch
	for sample_prep_entry in SamplePrepQueue.objects.filter(id__in=sample_prep_ids):
		existing_powder_batch = sample_prep_entry.powder_batch
		if existing_powder_batch == None or existing_powder_batch == powder_batch:
			sample_prep_entry.powder_batch = powder_batch
			sample_prep_entry.save(save_user=user)
			if sample_prep_entry.powder_sample != None:
				powder_sample = sample_prep_entry.powder_sample
				powder_sample.powder_batch = powder_batch
				powder_sample.save(save_user=user)
		else: # already assigned elsewhere
			failed_assignments[sample_prep_entry.id] = sample_prep_entry.powder_batch.name
	# assign reich lab sample number
	# Open is the state where samples can be added. If it is not open, then create the powder sample and assign Reich lab sample number
	if powder_batch.status not in [powder_batch.OPEN, powder_batch.STOP]:
		for sample_prep_entry in SamplePrepQueue.objects.filter(powder_batch=powder_batch).order_by('id'):
			new_reich_lab_powder_sample(sample_prep_entry, powder_batch, user)
	return failed_assignments

def ensure_powder_sample_reich_lab_sample_ids(lysate_batch):
	for lysate_batch_layout in lysate_batch.layout:
		powder_sample = lysate_batch_layout.powder_sample
		sample = powder_sample.sample
		sample.assign_reich_lab_sample_number()
