from django.db.models import Max

from .models import PowderSample, Sample

# create a PowderSample and assign Reich Lab Sample Number
def new_powder_sample(sample_queue_id, powder_batch):
	sample = Sample.objects.get(queue_id=sample_queue_id)
	# if the corresponding sample does not have Reich Lab sample number, then assign it the next one
	if sample.reich_lab_id is None:
		max_sample_number = Sample.objects.all().aggregate(Max('reich_lab_id'))['reich_lab_id__max']
		next_sample_number = max_sample_number + 1
		sample.reich_lab_id = next_sample_number
		#sample.save()
		return max_sample_number
	try:
		PowderSample.objects.get(sample=sample, powder_batch=powder_batch)
	except PowderSample.DoesNotExist:
		# count how many powder samples there for this sample
		existing_powder_samples = PowderSample.objects.filter(sample=sample)
		powder_sample_int = len(existing_powder_samples) + 1
		# TODO powder_sample_int should not be converted into a string. Model needs to be changed.
		powder_sample_id = f'S{sample.reich_lab_id}.P{powder_sample_int}'
		#PowderSample.objects.create(sample=sample, powder_batch=powder_batch, powder_sample_id=powder_sample_id)
