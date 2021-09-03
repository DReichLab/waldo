from .models. import ExtractBatch

# FIXME needed? layout is 

# assign 
def extract_batch_layout(extract_batch, control_layout_name):
	#PowdersToLayout = PowderSample.objects.filter()
	powders_to_layout = ExtractBatchLayout.objects.filter(extract_batch=extract_batch)
	
	controls = ControlLayout.objects.filter(layout_name=control_layout_name, control_type__control_type='Extract Negative')
	
	# count
	count = powders_to_layout.count() + controls.count()
	print(f'{count} extract batch layout elements')
	# This assumes a 96 well plate, which is how the model TimestampedWellPosition validates
	if count > 96:
		raise ValueError(f'{count} elements to layout for extract batch is greater than allowed 96')
	
	for layout_element in powders_to_layout:
		
