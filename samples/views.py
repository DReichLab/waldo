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
from samples.models import Results, Library, Sample, PowderBatch, WetLabStaff, PowderSample, ControlType, ControlLayout, ExtractionProtocol, ExtractBatch, SamplePrepQueue, PLATE_ROWS, ExtractBatchLayout
from .forms import IndividualForm, LibraryIDForm, PowderBatchForm, SampleImageForm, PowderSampleForm, PowderSampleFormset, ControlTypeFormset, ControlLayoutFormset, ExtractionProtocolFormset, ExtractBatchForm, SamplePrepQueueFormset, ExtractBatchLayoutForm
from sequencing_run.models import MTAnalysis

from .powder_samples import new_reich_lab_powder_sample, assign_prep_queue_entries_to_powder_batch, assign_powder_samples_to_extract_batch

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
	# TODO display recently changed batches
	return render(request, 'samples/landing.html', {} )

@login_required
def sample_prep_queue(request):
	page_number = request.GET.get('page', 1)
	page_size = request.GET.get('page_size', 25)
	whole_queue = SamplePrepQueue.objects.filter(powder_batch=None).order_by('priority')
	paginator = Paginator(whole_queue, page_size)
	page_obj = paginator.get_page(page_number)
	page_obj.ordered = True
	
	if request.method == 'POST':
		formset = SamplePrepQueueFormset(request.POST, request.FILES, form_kwargs={'user': request.user})
		
		if formset.is_valid():
			formset.save()
	elif request.method == 'GET':
		formset = SamplePrepQueueFormset(queryset=page_obj, form_kwargs={'user': request.user})
	
	return render(request, 'samples/generic_formset.html', { 'title': 'Sample Prep Queue', 'page_obj': page_obj, 'formset': formset, 'submit_button_text': 'Update queue entries' } )

@login_required
def sample_prep_queue_view(request):
	# show unassigned samples
	sample_queue = SamplePrepQueue.objects.filter(Q(powder_batch=None)).select_related('sample').select_related('sample_prep_protocol').order_by('priority')
	return render(request, 'samples/sample_prep_queue_view.html', { 'queued_samples': sample_queue } )

@login_required
def control_types(request):
	if request.method == 'POST':
		formset = ControlTypeFormset(request.POST, form_kwargs={'user': request.user})
		
		if formset.is_valid():
			formset.save()
		
	elif request.method == 'GET':
		page_number = request.GET.get('page', 1)
		page_size = request.GET.get('page_size', 25)
		whole_queue = ControlType.objects.all()
		paginator = Paginator(whole_queue, page_size)
		page_obj = paginator.get_page(page_number)
		page_obj.ordered = True
		formset = ControlTypeFormset(queryset=page_obj, form_kwargs={'user': request.user})
	return render(request, 'samples/generic_formset.html', { 'title': 'Control Types', 'page_obj': page_obj, 'formset': formset, 'submit_button_text': 'Update control types' } )

@login_required
def control_layout(request):
	if request.method == 'POST':
		formset = ControlLayoutFormset(request.POST, form_kwargs={'user': request.user})
		
		if formset.is_valid():
			formset.save()
		
	elif request.method == 'GET':
		page_number = request.GET.get('page', 1)
		page_size = request.GET.get('page_size', 25)
		whole_queue = ControlLayout.objects.all().order_by('layout_name')
		paginator = Paginator(whole_queue, page_size)
		page_obj = paginator.get_page(page_number)
		page_obj.ordered = True
		formset = ControlLayoutFormset(queryset=page_obj, form_kwargs={'user': request.user})
	return render(request, 'samples/generic_formset.html', { 'title': 'Control Layout', 'page_obj': page_obj, 'formset': formset, 'submit_button_text': 'Update control layout' } )

# show all powder batches
@login_required
def powder_batches(request):
	wetlab_staff = WetLabStaff.objects.get(login_user=request.user)
	form = PowderBatchForm(user=request.user, initial={'technician': wetlab_staff.initials()})
	
	if request.method == 'POST':
		form = PowderBatchForm(request.POST, user=request.user)
		if form.is_valid():
			powder_batch = form.save(commit=False)
			if not PowderBatch.objects.filter(pk=powder_batch.pk).exists():
				powder_batch.technician_fk = wetlab_staff
			powder_batch.save()
			return redirect(f'{reverse("powder_batch_assign_samples")}?name={powder_batch.name}')
		
	batches = PowderBatch.objects.all().annotate(Count('sampleprepqueue', distinct=True),
					Count('powdersample', distinct=True),
					low_complexity_count=Count('sampleprepqueue', distinct=True, filter=Q(sampleprepqueue__sample__expected_complexity__description__iexact='low')),
					high_complexity_count=Count('sampleprepqueue', distinct=True, filter=Q(sampleprepqueue__sample__expected_complexity__description__iexact='high')),
					).prefetch_related('extractbatch_set')
	return render(request, 'samples/powder_batches.html', {'powder_batches' : batches, 'form' : form} )

@login_required
def powder_batch_assign_samples(request):
	powder_batch_name = request.GET['name']
	powder_batch = PowderBatch.objects.get(name=powder_batch_name)
	if request.method == 'POST':
		form = PowderBatchForm(request.POST, user=request.user, instance=powder_batch)
		
		if form.is_valid():
			form.save()
			
			# these are the ticked checkboxes. Values are the ids of SamplePrepQueue objects
			sample_prep_ids = request.POST.getlist('sample_checkboxes[]')
			# accounting for sample prep queue and samples, including assigning Reich Lab sample ID
			assign_prep_queue_entries_to_powder_batch(powder_batch, sample_prep_ids, request.user)
			
			if powder_batch.status.description != 'Open':
				return redirect(f'{reverse("powder_samples")}?powder_batch={powder_batch_name}')
		
	elif request.method == 'GET':
		form = PowderBatchForm(user=request.user, initial={'name': powder_batch_name, 'date': powder_batch.date, 'status': powder_batch.status, 'notes': powder_batch.notes}, instance=powder_batch)
	
	# show samples assigned to this powder batch and unassigned samples
	sample_queue = SamplePrepQueue.objects.filter(Q(powder_batch=None, powder_sample=None) | Q(powder_batch=powder_batch)).select_related('sample').select_related('sample_prep_protocol').order_by('priority')
	# count for feedback
	num_sample_prep = SamplePrepQueue.objects.filter(powder_batch=powder_batch).count()
	num_powder_samples = PowderSample.objects.filter(powder_batch=powder_batch).count()
	return render(request, 'samples/sample_selection.html', { 'queued_samples': sample_queue, 'powder_batch_name': powder_batch_name, 'form': form, 'num_sample_prep': num_sample_prep, 'num_powder_samples': num_powder_samples } )

@login_required
def powder_samples(request):
	powder_batch_name = request.GET['powder_batch']
	powder_batch = PowderBatch.objects.get(name=powder_batch_name)
	if request.method == 'POST':
		powder_batch_form = PowderBatchForm(request.POST, instance=powder_batch, user=request.user)
		powder_batch_sample_formset = PowderSampleFormset(request.POST, request.FILES, form_kwargs={'user': request.user})
		
		if powder_batch_form.is_valid():
			powder_batch_form.save()
		if powder_batch_sample_formset.is_valid():
			powder_batch_sample_formset.save()
		if powder_batch_form.is_valid() and powder_batch_sample_formset.is_valid():
			if powder_batch.status.description == 'Open':
				return redirect(f'{reverse("powder_batch_assign_samples")}?name={powder_batch_name}')
		
	elif request.method == 'GET':
		powder_batch_form = PowderBatchForm(initial={'name': powder_batch_name, 'date': powder_batch.date, 'status': powder_batch.status, 'notes': powder_batch.notes}, instance=powder_batch, user=request.user)
		powder_batch_sample_formset = PowderSampleFormset(queryset=PowderSample.objects.filter(powder_batch=powder_batch), form_kwargs={'user': request.user})
	
	# open can have new samples assigned
	return render(request, 'samples/powder_samples.html', { 'powder_batch_name': powder_batch_name, 'powder_batch_form': powder_batch_form, 'formset': powder_batch_sample_formset} )

@login_required
def extraction_protocols(request):
	if request.method == 'POST':
		extraction_protocol_formset = ExtractionProtocolFormset(request.POST, request.FILES, form_kwargs={'user': request.user})
		if extraction_protocol_formset.is_valid():
			print('valid extraction protocol formset')
			extraction_protocol_formset.save()
		else:
			raise ValueError('failed validation')
		
	elif request.method == 'GET':
		extraction_protocol_formset = ExtractionProtocolFormset(queryset=ExtractionProtocol.objects.all(), form_kwargs={'user': request.user})
	
	# open can have new samples assigned
	return render(request, 'samples/extraction_protocols.html', { 'formset': extraction_protocol_formset } )

@login_required
def extract_batch (request):
	if request.method == 'POST':
		extract_batch_form = ExtractBatchForm(request.POST, user=request.user)
		if extract_batch_form.is_valid():
			extract_batch_instance = extract_batch_form.save(commit=False)
			if not ExtractBatch.objects.filter(pk=extract_batch_instance.pk).exists():
				if extract_batch_instance.technician_fk == None:
					wetlab_staff = WetLabStaff.objects.get(login_user=request.user)
					extract_batch_instance.technician_fk = wetlab_staff
					extract_batch_instance.technician = wetlab_staff.initials()
			extract_batch_instance.save()
		
	elif request.method == 'GET':
		extract_batch_form = ExtractBatchForm(user=request.user)
	
	extract_batches = ExtractBatch.objects.all()
	# open can have new samples assigned
	return render(request, 'samples/extract_batch.html', { 'extract_batch_form': extract_batch_form, 'extract_batches': extract_batches } )

@login_required
def extract_batch_assign_powder(request):
	extract_batch_name = request.GET['extract_batch']
	extract_batch = ExtractBatch.objects.get(batch_name=extract_batch_name)
	if request.method == 'POST':
		extract_batch_form = ExtractBatchForm(request.POST, instance=extract_batch, user=request.user)
		if extract_batch_form.is_valid():
			print('valid extract_batch form')
			extract_batch_form.save()
			
			# iterate through the checkboxes and change states
			ticked_checkboxes = request.POST.getlist('powder_sample_checkboxes[]')
			# tickbox name is powder sample id
			assign_powder_samples_to_extract_batch(extract_batch, ticked_checkboxes, request.user)
			#for powder_sample_id in ticked_checkboxes:
			#	print(f'powder sample: {powder_sample_id}')
		
	elif request.method == 'GET':
		extract_batch_form = ExtractBatchForm(instance=extract_batch, user=request.user)
	
	already_selected_powder_sample_ids = ExtractBatchLayout.objects.filter(extract_batch=extract_batch).values_list('powder_sample', flat=True)
	powder_samples_already_selected = PowderSample.objects.annotate(num_assignments=Count('extractbatchlayout')).annotate(assigned_to_extract_batch=Count('extractbatchlayout', filter=Q(extractbatchlayout__extract_batch=extract_batch))).filter(
		Q(id__in=already_selected_powder_sample_ids)
	)
	powder_samples_unselected = PowderSample.objects.annotate(num_assignments=Count('extractbatchlayout')).annotate(assigned_to_extract_batch=Count('extractbatchlayout', filter=Q(extractbatchlayout__extract_batch=extract_batch))).filter(
		Q(powder_batch__status__description='Ready For Plate', num_assignments=0)
		| (Q(powder_batch=None) & ~Q(powder_sample_id__endswith='NP'))# powder samples directly from collaborators will not have powder batch. Exclude controls. 
	)
	powder_samples = powder_samples_already_selected.union(powder_samples_unselected).order_by('id')
	
	assigned_powder_samples_count = already_selected_powder_sample_ids.count()
	
	return render(request, 'samples/extract_batch_assign_powder.html', { 'extract_batch_name': extract_batch_name, 'powder_samples': powder_samples, 'assigned_powder_samples_count': assigned_powder_samples_count, 'form': extract_batch_form  } )

@login_required
def extract_batch_assign_powder_batches(request):
	extract_batch_name = request.GET['extract_batch']
	extract_batch = ExtractBatch.objects.get(batch_name=extract_batch_name)
	if request.method == 'POST':
		extract_batch_form = ExtractBatchForm(request.POST, instance=extract_batch, user=request.user)
		if extract_batch_form.is_valid():
			extract_batch_form.save()
			
			# assign powder batches to ManyToMany field
			ticked_checkboxes = request.POST.getlist('checkboxes[]')
			#print(ticked_checkboxes)
			selected_powder_batches = PowderBatch.objects.filter(name__in=ticked_checkboxes)
			extract_batch.powder_batches.set(selected_powder_batches)
		
	elif request.method == 'GET':
		extract_batch_form = ExtractBatchForm(instance=extract_batch, user=request.user)
	
	num_powder_samples_assigned = extract_batch.num_powder_samples()
	# provide template with how many powder samples in each powder batch and indicate whether powder batch is associated with this extract batch
	powder_batches = PowderBatch.objects.annotate(Count('sampleprepqueue', distinct=True),
					checked=Count('extractbatch', filter=Q(extractbatch=extract_batch)),
					low_complexity_count=Count('sampleprepqueue', distinct=True, filter=Q(sampleprepqueue__sample__expected_complexity__description__iexact='low')),
					high_complexity_count=Count('sampleprepqueue', distinct=True, filter=Q(sampleprepqueue__sample__expected_complexity__description__iexact='high')),
					).filter(Q(status__description='Ready For Plate') & (Q(extractbatch=None) | Q(extractbatch=extract_batch)))
	
	#print(f'num powder batches {len(powder_batches)}')
	return render(request, 'samples/extract_batch_assign_powder_batches.html', { 'extract_batch_name': extract_batch_name,  'num_powder_samples_assigned': num_powder_samples_assigned, 'powder_batches': powder_batches, 'form': extract_batch_form } )

def reich_lab_sample_number_from_string(s):
	if s.startswith('S'):
		return int(s[1:])
	else:
		return int(s)

@login_required
def sample(request):
	form = SampleImageForm()
	if request.method == 'POST':
		form = SampleImageForm(request.POST, request.FILES)
		if form.is_valid():
			reich_lab_sample_number = reich_lab_sample_number_from_string(request.GET['sample'])
			print(reich_lab_sample_number)
			photo = request.FILES.get('photo')
			label = form.cleaned_data['image_type']
			save_sample_photo(photo, reich_lab_sample_number, label)
		else:
			print('invalid sample photo form')
		
	elif request.method == 'GET':
		# database, not Reich Lab ID
		reich_lab_sample_number = reich_lab_sample_number_from_string(request.GET['sample'])
	
	images = photo_list(reich_lab_sample_number)
	return render(request, 'samples/sample.html', { 'reich_lab_sample_number': reich_lab_sample_number, 'images': images, 'form': form} )

PLATE_ROWS = 'ABCDEFGH'
WELL_PLATE_COLUMNS = range(1,13)

# Assign well locations to powder samples
@login_required
def extract_batch_plate_layout_initial(request):
	extract_batch_name = request.GET['extract_batch_name']
	
	if request.method == 'POST':
		form = ExtractBatchLayoutForm(request.POST)
		if form.is_valid():
			extract_batch = ExtractBatch.objects.get(batch_name=extract_batch_name)
			control_layout_name = form.cleaned_data['control_layout']
			print(f'layout {extract_batch_name} {control_layout_name}')
			extract_batch.assign_layout(control_layout_name, request.user)
			return redirect(f'{reverse("extract_batch_plate_layout")}?extract_batch_name={extract_batch_name}')
	else:
		form = ExtractBatchLayoutForm()
		form.name = extract_batch_name
		
	return render(request, 'samples/extract_batch_plate_layout_initial.html', {'extract_batch_name': extract_batch_name, 'form': form})
		

@login_required
def extract_batch_plate_layout(request):
	try:
		extract_batch_name = request.GET['extract_batch_name']
	except:
		extract_batch_name = request.POST['extract_batch_name']
	extract_batch = ExtractBatch.objects.get(batch_name=extract_batch_name)
	
	if request.method == 'POST' and request.is_ajax():
		# JSON for a well plate layout
		print(request.body)
		layout = request.POST['layout']
		objects_map = json.loads(layout)
		# TODO propagate changes to database
		print('ajax submission')
	elif request.method == 'POST':
		#control_layout_name = request.POST['control_layout_name']
		#extract_batch.assign_layout(control_layout_name, request.user)
		print('POST {extract_batch_name}')
		
	layout_elements = ExtractBatchLayout.objects.filter(extract_batch=extract_batch).select_related('powder_sample').select_related('control_type')
		
	objects_map = {}
	for layout_element in layout_elements:
		if layout_element.powder_sample != None:
			identifier = layout_element.powder_sample.powder_sample_id
		elif layout_element.control_type != None:
			# label with location to distinguish between controls
			identifier = f'{layout_element.control_type.control_type} {str(layout_element)}'
		else:
			raise ValueError('ExtractBatchLayout with neither powder sample nor control content f{layout_element.pk}')
		# remove spaces and periods for HTML widget
		joint = { 'position':f'{str(layout_element)}', 'widget_id':identifier.replace(' ','').replace('.','') }
		objects_map[identifier] = joint
		
	return render(request, 'samples/extract_batch_plate_layout.html', { 'extract_batch_name': extract_batch_name, 'rows':PLATE_ROWS, 'columns':WELL_PLATE_COLUMNS, 'objects_map': objects_map } )
	
# Handle the layout of a 96 well plate with libraries
# This renders an interface allowing a technician to move libraries between wells
@login_required
def well(request):
	if request.method == 'POST' and request.is_ajax():
		# JSON for a well plate layout
		libraries_map = json.loads(request.body)
		
		return render(request, 'samples/well_plate.html', { 'rows':PLATE_ROWS, 'columns':WELL_PLATE_COLUMNS, 'libraries_map':libraries_map} )
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
			
		return render(request, 'samples/well_plate.html', { 'rows':PLATE_ROWS, 'columns':WELL_PLATE_COLUMNS, 'libraries_map':libraries_map} )
		
def logout_user(request):
	return logout_then_login(request)

@login_required
def password_changed(request):
	return render(request, 'samples/password_changed.html', {} )
