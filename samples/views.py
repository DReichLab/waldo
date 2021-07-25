from django.core.paginator import Paginator
from django.shortcuts import redirect, render, reverse

from django.http import HttpResponse

from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import logout_then_login

from django.db.models import Q, Count

import csv
import json
from datetime import datetime

from samples.pipeline import udg_and_strandedness
from samples.models import Results, Library, Sample, PowderBatch, WetLabStaff, PowderSample, ControlType, ControlLayout, ExtractionProtocol, ExtractBatch, SamplePrepQueue
from .forms import IndividualForm, LibraryIDForm, PowderBatchForm, SampleImageForm, PowderSampleForm, PowderSampleFormset, ControlTypeFormset, ControlLayoutFormset, ExtractionProtocolFormset, ExtractBatchForm, SamplePrepQueueFormset
from sequencing_run.models import MTAnalysis

from .powder_samples import new_reich_lab_powder_sample

from samples.sample_photos import photo_list, save_sample_photo

# Create your views here.

def query(request):
	if request.method == 'POST':
		form = IndividualForm(request.POST)
		if form.is_valid():
			individual_id = form.cleaned_data['individual_id']
			
			response = HttpResponse(content_type='text/csv')
			response['Content-Disposition'] = 'attachment; filename="results.csv"'

			writer = csv.writer(response, delimiter='\t')
			writer.writerow(["This will be a query result for {:d}.".format(individual_id), '{:d}'.format(individual_id)])
			return response
		else:
			return HttpResponse("Invalid form")
	else:
		form = IndividualForm()
		return render(request, 'samples/simple_query.html', {'form': form})
	
# input: a library ID (for example: S17806.Y1.E1.L1)
# output: instance ID for David's anno file
#	If there are prior libraries for this individual, this should be the library ID
# 	If this is the first library, this should be the individual (I17806)
def library_id_to_instance(request):
	if request.method == 'POST':
		form = LibraryIDForm(request.POST)
		if form.is_valid():
			library_id = form.cleaned_data['library_id']
			
			response = HttpResponse(content_type='text/csv')
			response['Content-Disposition'] = 'attachment; filename="results.csv"'

			writer = csv.writer(response, delimiter='\t')
			writer.writerow(["This will be a query result for {}.".format(library_id), '{}'.format(library_id)])
			return response
		else:
			return HttpResponse("Invalid form")
	else:
		form = LibraryIDForm()
		return render(request, 'samples/simple_query.html', {'form': form})

def mt_results(library_id, damage_restricted=False):
	results = Results.objects.get(library_id__exact=library_id)
	library = Library.objects.get(reich_lab_library_id = library_id)
	udg, strandedness = udg_and_strandedness(library)
	
	# MTAnalysis
	mt = MTAnalysis.objects.get(parent = results, damage_restricted = damage_restricted)
	return mt

def mt_query(request):
	if request.method == 'POST':
		form = LibraryIDForm(request.POST)
		if form.is_valid():
			library_id = form.cleaned_data['library_id']
			mt = mt_results(library_id)
			
			return render(request, 'samples/library_mt.html', {'form': form, 'mt_results': [mt]})
		else:
			return HttpResponse("Invalid form")
	else:
		form = LibraryIDForm()
		return render(request, 'samples/library_mt.html', {'form': form})
	
@login_required
def landing(request):
	return render(request, 'samples/landing.html', {} )

@login_required
def sample_prep_queue(request):
	page_number = request.GET.get('page', 1)
	page_size = request.GET.get('page_size', 25)
	whole_queue = SamplePrepQueue.objects.filter(powder_batch=None).order_by('-priority')
	paginator = Paginator(whole_queue, page_size)
	page_obj = paginator.get_page(page_number)
	page_obj.ordered = True
	
	if request.method == 'POST':
		formset = SamplePrepQueueFormset(request.POST, request.FILES)
		
		if formset.is_valid():
			formset.save()
	elif request.method == 'GET':
		formset = SamplePrepQueueFormset(queryset=page_obj)
	
	return render(request, 'samples/generic_formset.html', { 'title': 'Sample Prep Queue', 'page_obj': page_obj, 'formset': formset, 'submit_button_text': 'Update queue entries' } )

@login_required
def control_types(request):
	if request.method == 'POST':
		formset = ControlTypeFormset(request.POST)
		
		if formset.is_valid():
			formset.save()
		
	elif request.method == 'GET':
		page_number = request.GET.get('page', 1)
		page_size = request.GET.get('page_size', 25)
		whole_queue = ControlType.objects.all()
		paginator = Paginator(whole_queue, page_size)
		page_obj = paginator.get_page(page_number)
		page_obj.ordered = True
		formset = ControlTypeFormset(queryset=page_obj)
	return render(request, 'samples/generic_formset.html', { 'title': 'Control Types', 'page_obj': page_obj, 'formset': formset, 'submit_button_text': 'Update control types' } )

@login_required
def control_layout(request):
	if request.method == 'POST':
		formset = ControlLayoutFormset(request.POST)
		
		if formset.is_valid():
			formset.save()
		
	elif request.method == 'GET':
		page_number = request.GET.get('page', 1)
		page_size = request.GET.get('page_size', 25)
		whole_queue = ControlLayout.objects.all()
		paginator = Paginator(whole_queue, page_size)
		page_obj = paginator.get_page(page_number)
		page_obj.ordered = True
		formset = ControlLayoutFormset(queryset=page_obj)
	return render(request, 'samples/generic_formset.html', { 'title': 'Control Layout', 'page_obj': page_obj, 'formset': formset, 'submit_button_text': 'Update control layout' } )

# show all powder batches
@login_required
def powder_batches(request):
	form = PowderBatchForm()
	
	if request.method == 'POST':
		form = PowderBatchForm(request.POST)
		if form.is_valid():
			name = form.cleaned_data['name']
			date = form.cleaned_data['date']
			status = form.cleaned_data['status']
			notes = form.cleaned_data['notes']
			
			powder_batch, created = PowderBatch.objects.get_or_create(name=name)
			powder_batch.date = date
			if created:
				wetlab_staff = WetLabStaff.objects.get(login_user=request.user)
				powder_batch.technician_fk = wetlab_staff
				powder_batch.technician = wetlab_staff.initials()
			powder_batch.status = status
			powder_batch.notes = notes
			powder_batch.save()
		else:
			return HttpResponse("Invalid form")
		
	batches = PowderBatch.objects.all()
	return render(request, 'samples/powder_batches.html', {'powder_batches' : batches, 'form' : form} )

@login_required
def powder_batch_assign_samples(request):
	powder_batch_name = request.GET['name']
	powder_batch = PowderBatch.objects.get(name=powder_batch_name)
	if request.method == 'POST':
		form = PowderBatchForm(request.POST, instance=powder_batch)
		
		if form.is_valid():
			form.save()
			
			# these are the ticked checkboxes. Values are the ids of SamplePrepQueue objects
			ticked_checkboxes = request.POST.getlist('sample_checkboxes[]')
			# first clear powder batch
			to_clear = SamplePrepQueue.objects.filter(powder_batch=powder_batch).exclude(id__in=ticked_checkboxes)
			for sample_prep_entry in to_clear:
				sample_prep_entry.powder_batch = None
				sample_prep_entry.save()
			# add ticked samples to powder batch
			for sample_prep_entry in SamplePrepQueue.objects.filter(id__in=ticked_checkboxes):
				if sample_prep_entry.powder_batch == None:
					sample_prep_entry.powder_batch = powder_batch
					sample_prep_entry.save()
			# assign reich lab sample number
			if powder_batch.status.description != 'Open':
				for sample_prep_entry in SamplePrepQueue.objects.filter(powder_batch=powder_batch):
					new_reich_lab_powder_sample(sample_prep_entry.sample.queue_id, powder_batch, sample_prep_entry)
				return redirect(f'{reverse("powder_samples")}?powder_batch={powder_batch_name}')
		
	elif request.method == 'GET':
		form = PowderBatchForm(initial={'name': powder_batch_name, 'date': powder_batch.date, 'status': powder_batch.status, 'notes': powder_batch.notes}, instance=powder_batch)
	
	# show samples assigned to this powder batch and unassigned samples
	sample_queue = SamplePrepQueue.objects.filter(Q(powder_batch=None) | Q(powder_batch=powder_batch)).select_related('sample').select_related('expected_complexity').select_related('sample_prep_protocol').order_by('-priority')
	return render(request, 'samples/sample_selection.html', { 'queued_samples': sample_queue, 'powder_batch_name': powder_batch_name, 'form': form } )

@login_required
def powder_samples(request):
	powder_batch_name = request.GET['powder_batch']
	powder_batch = PowderBatch.objects.get(name=powder_batch_name)
	if request.method == 'POST':
		powder_batch_form = PowderBatchForm(request.POST, instance=powder_batch)
		powder_batch_sample_formset = PowderSampleFormset(request.POST, request.FILES)
		
		if powder_batch_form.is_valid():
			powder_batch_form.save()
		if powder_batch_sample_formset.is_valid():
			powder_batch_sample_formset.save()
		if powder_batch_form.is_valid() and powder_batch_sample_formset.is_valid():
			if powder_batch.status.description == 'Open':
				return redirect(f'{reverse("powder_batch_assign_samples")}?name={powder_batch_name}')
		
	elif request.method == 'GET':
		powder_batch_form = PowderBatchForm(initial={'name': powder_batch_name, 'date': powder_batch.date, 'status': powder_batch.status, 'notes': powder_batch.notes}, instance=powder_batch)
		powder_batch_sample_formset = PowderSampleFormset(queryset=PowderSample.objects.filter(powder_batch=powder_batch))
	
	# open can have new samples assigned
	return render(request, 'samples/powder_samples.html', { 'powder_batch_name': powder_batch_name, 'powder_batch_form': powder_batch_form, 'formset': powder_batch_sample_formset} )

@login_required
def extraction_protocols(request):
	if request.method == 'POST':
		extraction_protocol_formset = ExtractionProtocolFormset(request.POST, request.FILES)
		if extraction_protocol_formset.is_valid():
			print('valid extraction protocol formset')
			extraction_protocol_formset.save()
		else:
			raise ValueError('failed validation')
		
	elif request.method == 'GET':
		extraction_protocol_formset = ExtractionProtocolFormset(queryset=ExtractionProtocol.objects.all())
	
	# open can have new samples assigned
	return render(request, 'samples/extraction_protocols.html', { 'formset': extraction_protocol_formset } )

@login_required
def extract_batch (request):
	if request.method == 'POST':
		extract_batch_form = ExtractBatchForm(request.POST)
		if extract_batch_form.is_valid():
			extract_batch_form.save()
		
	elif request.method == 'GET':
		extract_batch_form = ExtractBatchForm()
	
	extract_batches = ExtractBatch.objects.all()
	# open can have new samples assigned
	return render(request, 'samples/extract_batch.html', { 'extract_batch_form': extract_batch_form, 'extract_batches': extract_batches } )

@login_required
def extract_batch_assign_powder(request):
	extract_batch_name = request.GET['extract_batch']
	extract_batch = ExtractBatch.objects.get(batch_name=extract_batch_name)
	if request.method == 'POST':
		extract_batch_form = ExtractBatchForm(request.POST, instance=extract_batch)
		if extract_batch_form.is_valid():
			extract_batch_form.save()
			
			# iterate through the checkboxes and change states
			ticked_checkboxes = request.POST.getlist('checkboxes[]')
			#TODO
		
	elif request.method == 'GET':
		extract_batch_form = ExtractBatchForm(instance=extract_batch)
	
	# TODO
	powder_samples = PowderSample.objects.filter(Q(powder_batch__status__description='Ready For Plate')  )
	# open can have new samples assigned
	return render(request, 'samples/extract_batch_assign_powder.html', { 'powder_samples': powder_samples } )

@login_required
def extract_batch_assign_powder_batches(request):
	extract_batch_name = request.GET['extract_batch']
	extract_batch = ExtractBatch.objects.get(batch_name=extract_batch_name)
	if request.method == 'POST':
		extract_batch_form = ExtractBatchForm(request.POST, instance=extract_batch)
		if extract_batch_form.is_valid():
			extract_batch_form.save()
			
			# assign powder batches to ManyToMany field
			ticked_checkboxes = request.POST.getlist('checkboxes[]')
			print(ticked_checkboxes)
			selected_powder_batches = PowderBatch.objects.filter(name__in=ticked_checkboxes)
			extract_batch.powder_batches.set(selected_powder_batches)
		
	elif request.method == 'GET':
		extract_batch_form = ExtractBatchForm(instance=extract_batch)
	# count the number of samples in powder batches for this extract batch
	num_powder_samples_assigned = 0
	for powder_batch in extract_batch.powder_batches.all():
		num_powder_samples_assigned += PowderSample.objects.filter(powder_batch=powder_batch).count()
	
	# provide template with how many powder samples in each powder batch and indicate whether powder batch is associated with this extract batch
	powder_batches = PowderBatch.objects.annotate(Count('powdersample'), checked=Count('extractbatch', filter=Q(extractbatch=extract_batch))).filter(Q(status__description='Ready For Plate') | Q(extractbatch=extract_batch))
	#print(f'num powder batches {len(powder_batches)}')
	return render(request, 'samples/extract_batch_assign_powder_batches.html', { 'extract_batch_name': extract_batch_name,  'num_powder_samples_assigned': num_powder_samples_assigned, 'powder_batches': powder_batches, 'form': extract_batch_form } )

@login_required
def extract_batch_plate_layout(request):
	return render(request, 'samples/extract_batch_plate_layout.html', { 'powder_samples': powder_samples } )

@login_required
def sample(request):
	form = SampleImageForm()
	if request.method == 'POST':
		form = SampleImageForm(request.POST, request.FILES)
		if form.is_valid():
			reich_lab_sample_number = int(request.GET['sample'])
			print(reich_lab_sample_number)
			photo = request.FILES.get('photo')
			label = form.cleaned_data['image_type']
			save_sample_photo(photo, reich_lab_sample_number, label)
		else:
			print('invalid sample photo form')
		
	elif request.method == 'GET':
		# database, not Reich Lab ID
		reich_lab_sample_number = int(request.GET['sample'])
	
	images = photo_list(reich_lab_sample_number)
	return render(request, 'samples/sample.html', { 'reich_lab_sample_number': reich_lab_sample_number, 'images': images, 'form': form} )
	
# Handle the layout of a 96 well plate with libraries
# This renders an interface allowing a technician to move libraries between wells
@login_required
def well(request):
	well_plate_rows = 'ABCDEFGH'
	well_plate_columns = range(1,13)
	
	if request.method == 'POST' and request.is_ajax():
		# JSON for a well plate layout
		libraries_map = json.loads(request.body)
		
		return render(request, 'samples/well_plate.html', { 'rows':well_plate_rows, 'columns':well_plate_columns, 'libraries_map':libraries_map} )
	else:
		library_id_list = ['S20000.Y1.E1.L1', 'S2234.E1.L1']
		libraries_map = {}
		counter = 1
		for library_id in library_id_list:
			joint = { 'position':f'A{counter}', 'widget_id':library_id.replace('.','') }
			counter += 1
			libraries_map[library_id] = joint
			
		for key, value in libraries_map.items():
			print(f'{key}\t{value}')
			
		return render(request, 'samples/well_plate.html', { 'rows':well_plate_rows, 'columns':well_plate_columns, 'libraries_map':libraries_map} )
		
def logout_user(request):
	return logout_then_login(request)

@login_required
def password_changed(request):
	return render(request, 'samples/password_changed.html', {} )
