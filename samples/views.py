from django.core.paginator import Paginator
from django.shortcuts import redirect, render, reverse

from django.http import HttpResponse, HttpResponseBadRequest

from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import logout_then_login

from django.db.models import Q, Count

import csv
import json
from datetime import datetime

from samples.pipeline import udg_and_strandedness
from samples.models import Results, Library, Sample, PowderBatch, WetLabStaff, PowderSample, ControlType, ControlSet, ControlLayout, ExtractionProtocol, LysateBatch, SamplePrepQueue, PLATE_ROWS, LysateBatchLayout, ExtractionBatch, ExtractionBatchLayout, Lysate, LibraryBatch, LibraryBatchLayout, Extract, Storage
from .forms import IndividualForm, LibraryIDForm, PowderBatchForm, SampleImageForm, PowderSampleForm, PowderSampleFormset, ControlTypeFormset, ControlSetForm, ControlLayoutFormset, ExtractionProtocolFormset, LysateBatchForm, LysateFormset, LysateForm, SamplePrepQueueFormset, LostPowderFormset, SpreadsheetForm, LysateBatchToExtractBatchForm, ExtractionBatchForm, LostLysateFormset, ExtractBatchToLibraryBatchForm, LibraryBatchForm, StorageFormset, ExtractFormset, LibraryFormset
from sequencing_run.models import MTAnalysis

from .powder_samples import new_reich_lab_powder_sample, assign_prep_queue_entries_to_powder_batch, assign_powder_samples_to_lysate_batch, powder_samples_from_spreadsheet, assign_lysates_to_extract_batch
from .layout import duplicate_positions_check, update_db_layout,  layout_objects_map_for_rendering, occupied_wells

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
	page_number = request.GET.get('page', 1)
	page_size = request.GET.get('page_size', 25)
	whole_queue = ControlLayout.objects.all().order_by('layout_name')
	paginator = Paginator(whole_queue, page_size)
	page_obj = paginator.get_page(page_number)
	page_obj.ordered = True
		
	if request.method == 'POST':
		formset = ControlLayoutFormset(request.POST, form_kwargs={'user': request.user})
		
		if formset.is_valid():
			formset.save()
		
	elif request.method == 'GET':
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
					)
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
	return render(request, 'samples/powder_batch_assign_sample.html', { 'queued_samples': sample_queue, 'powder_batch_name': powder_batch_name, 'form': form, 'num_sample_prep': num_sample_prep, 'num_powder_samples': num_powder_samples } )

# Edit the powder samples in a powder batch
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
		# do not require the formset to be valid to switch back to open
		if powder_batch_form.is_valid() and powder_batch.status.description == 'Open':
				return redirect(f'{reverse("powder_batch_assign_samples")}?name={powder_batch_name}')
		
	elif request.method == 'GET':
		powder_batch_form = PowderBatchForm(initial={'name': powder_batch_name, 'date': powder_batch.date, 'status': powder_batch.status, 'notes': powder_batch.notes}, instance=powder_batch, user=request.user)
		powder_batch_sample_formset = PowderSampleFormset(queryset=PowderSample.objects.filter(powder_batch=powder_batch), form_kwargs={'user': request.user})
	
	# open can have new samples assigned
	return render(request, 'samples/powder_samples.html', { 'powder_batch_name': powder_batch_name, 'powder_batch_form': powder_batch_form, 'formset': powder_batch_sample_formset} )
	
# return a spreadsheet version of data for offline editing
@login_required
def powder_samples_spreadsheet(request):
	powder_batch_name = request.GET['powder_batch_name']
	powder_batch = PowderBatch.objects.get(name=powder_batch_name)
	
	response = HttpResponse(content_type='text/csv')
	response['Content-Disposition'] = f'attachment; filename="powder_batch_{powder_batch_name}.tsv"'

	writer = csv.writer(response, delimiter='\t')
	# header
	writer.writerow(PowderSample.spreadsheet_header())
	powder_samples = PowderSample.objects.filter(powder_batch=powder_batch)
	for powder_sample in powder_samples:
		writer.writerow(powder_sample.to_spreadsheet_row())
	return response
	
@login_required
def powder_samples_spreadsheet_upload(request):
	powder_batch_name = request.GET['powder_batch_name']
	if request.method == 'POST':
		spreadsheet_form = SpreadsheetForm(request.POST, request.FILES)
		print(f'powder sample spreadsheet {powder_batch_name}')
		if spreadsheet_form.is_valid():
			spreadsheet = request.FILES.get('spreadsheet')
			powder_samples_from_spreadsheet(powder_batch_name, spreadsheet, request.user)
			message = 'Values updated'
	else:
		spreadsheet_form = SpreadsheetForm()
		message = ''
	return render(request, 'samples/spreadsheet_upload.html', { 'title': f'Powder batch samples for {powder_batch_name}', 'form': spreadsheet_form, 'message': message} )

@login_required
def extraction_protocols(request):
	if request.method == 'POST':
		extraction_protocol_formset = ExtractionProtocolFormset(request.POST, request.FILES, form_kwargs={'user': request.user})
		if extraction_protocol_formset.is_valid():
			print('valid extraction protocol formset')
			extraction_protocol_formset.save()
		
	elif request.method == 'GET':
		extraction_protocol_formset = ExtractionProtocolFormset(queryset=ExtractionProtocol.objects.all(), form_kwargs={'user': request.user})
	
	# open can have new samples assigned
	return render(request, 'samples/extraction_protocols.html', { 'formset': extraction_protocol_formset } )
	
@login_required
def control_sets(request):
	control_sets_all = ControlSet.objects.all().order_by('layout_name')
	
	if request.method == 'POST':
		form  = ControlSetForm(request.POST, user=request.user)
		if form.is_valid():
			form.save()
		
	elif request.method == 'GET':
		form = ControlSetForm(user=request.user)
	# open can have new samples assigned
	return render(request, 'samples/control_sets.html', { 'form': form, 'control_sets': control_sets_all } )
	
@login_required
def control_set(request):
	control_set_name = request.GET['control_set_name']
	control_set_instance = ControlSet.objects.get(layout_name=control_set_name)
	
	if request.method == 'POST':
		form  = ControlSetForm(request.POST, instance=control_set_instance, user=request.user)
		formset = ControlLayoutFormset(request.POST, request.FILES, form_kwargs={'user': request.user})
		if form.is_valid():
			form.save()
		if formset.is_valid():
			formset.save()
		
	elif request.method == 'GET':
		
		form = ControlSetForm(instance=control_set_instance, user=request.user)
		formset = ControlLayoutFormset(queryset=ControlLayout.objects.filter(control_set=control_set_instance), form_kwargs={'user': request.user})
	
	return render(request, 'samples/control_set.html', { 'form': form, 'formset': formset, 'layout_name': control_set_name } )

@login_required
def lysate_batch (request):
	if request.method == 'POST':
		lysate_batch_form = LysateBatchForm(request.POST, user=request.user)
		if lysate_batch_form.is_valid():
			lysate_batch_instance = lysate_batch_form.save(commit=False)
			if not LysateBatch.objects.filter(pk=lysate_batch_instance.pk).exists():
				if lysate_batch_instance.technician_fk == None:
					wetlab_staff = WetLabStaff.objects.get(login_user=request.user)
					lysate_batch_instance.technician_fk = wetlab_staff
					lysate_batch_instance.technician = wetlab_staff.initials()
			lysate_batch_instance.save()
		
	elif request.method == 'GET':
		lysate_batch_form = LysateBatchForm(user=request.user)
	
	lysate_batches = LysateBatch.objects.all().order_by('status', '-date')
	# open can have new samples assigned
	return render(request, 'samples/lysate_batch.html', { 'lysate_batch_form': lysate_batch_form, 'lysate_batches': lysate_batches } )

@login_required
def lysate_batch_assign_powder(request):
	lysate_batch_name = request.GET['lysate_batch_name']
	lysate_batch = LysateBatch.objects.get(batch_name=lysate_batch_name)
	if request.method == 'POST':
		lysate_batch_form = LysateBatchForm(request.POST, instance=lysate_batch, user=request.user)
		if lysate_batch_form.is_valid():
			print('valid lysate_batch form')
			lysate_batch_form.save()
			
			# iterate through the checkboxes and change states
			ticked_checkboxes = request.POST.getlist('powder_sample_checkboxes[]')
			# tickbox name is powder sample object id (int)
			#for powder_sample_id in ticked_checkboxes:
			#	print(f'powder sample: {powder_sample_id}')
			assign_powder_samples_to_lysate_batch(lysate_batch, ticked_checkboxes, request.user)
			if 'assign_and_layout' in request.POST:
				print(f'lysate batch layout {lysate_batch_name}')
				lysate_batch.assign_layout(request.user)
				return redirect(f'{reverse("lysate_batch_plate_layout")}?lysate_batch_name={lysate_batch_name}')
			elif 'assign_and_fill_empty_with_library_controls' in request.POST:
				print(f'lysate batch layout {lysate_batch_name}')
				lysate_batch.fill_empty_wells_with_library_negatives(request.user)
				return redirect(f'{reverse("lysate_batch_plate_layout")}?lysate_batch_name={lysate_batch_name}')
			elif lysate_batch.status == lysate_batch.LYSATES_CREATED:
				lysate_batch.create_lysates(request.user)
				return redirect(f'{reverse("lysates_in_batch")}?lysate_batch_name={lysate_batch_name}')
		
	elif request.method == 'GET':
		lysate_batch_form = LysateBatchForm(instance=lysate_batch, user=request.user)
		
	existing_controls = LysateBatchLayout.objects.filter(lysate_batch=lysate_batch, control_type__isnull=False)
	
	already_selected_powder_sample_ids = LysateBatchLayout.objects.filter(lysate_batch=lysate_batch, control_type=None).values_list('powder_sample', flat=True)
	powder_samples_already_selected = PowderSample.objects.annotate(num_assignments=Count('lysatebatchlayout')).annotate(assigned_to_lysate_batch=Count('lysatebatchlayout', filter=Q(lysatebatchlayout__lysate_batch=lysate_batch))).filter(
		Q(id__in=already_selected_powder_sample_ids)
	)
	powder_samples_unselected = PowderSample.objects.annotate(num_assignments=Count('lysatebatchlayout')).annotate(assigned_to_lysate_batch=Count('lysatebatchlayout', filter=Q(lysatebatchlayout__lysate_batch=lysate_batch))).filter(
		Q(powder_batch__status__description='Ready For Plate', num_assignments=0)
		| (Q(powder_batch=None) & ~Q(powder_sample_id__endswith='NP'))# powder samples directly from collaborators will not have powder batch. Exclude controls. 
	)
	powder_samples = powder_samples_already_selected.union(powder_samples_unselected).order_by('id')
	
	assigned_powder_samples_count = already_selected_powder_sample_ids.count()
	# count wells
	occupied_well_count, num_non_control_assignments = occupied_wells(LysateBatchLayout.objects.filter(lysate_batch=lysate_batch))
	
	return render(request, 'samples/lysate_batch_assign_powder.html', { 'lysate_batch_name': lysate_batch_name, 'powder_samples': powder_samples, 'assigned_powder_samples_count': assigned_powder_samples_count, 'control_count': len(existing_controls), 'num_assignments': num_non_control_assignments, 'occupied_wells': occupied_well_count, 'form': lysate_batch_form  } )
	
@login_required
def lysates_in_batch(request):
	lysate_batch_name = request.GET['lysate_batch_name']
	lysate_batch = LysateBatch.objects.get(batch_name=lysate_batch_name)
	
	if request.method == 'POST':
		lysate_batch_form = LysateBatchForm(request.POST, instance=lysate_batch, user=request.user)
		lysates_formset = LysateFormset(request.POST, request.FILES, form_kwargs={'user': request.user})
		
		if lysate_batch_form.is_valid():
			lysate_batch_form.save()
		if lysates_formset.is_valid():
			lysates_formset.save()
		if lysate_batch_form.is_valid() and lysates_formset.is_valid():
			if lysate_batch.status == lysate_batch.OPEN:
				return redirect(f'{reverse("lysate_batch_assign_powder")}?lysate_batch_name={lysate_batch_name}')
		
	elif request.method == 'GET':
		#powder_batch_form = PowderBatchForm(initial={'name': powder_batch_name, 'date': powder_batch.date, 'status': powder_batch.status, 'notes': powder_batch.notes}, instance=powder_batch, user=request.user)
		lysate_batch_form = LysateBatchForm(instance=lysate_batch, user=request.user)
		lysates_formset = LysateFormset(queryset=Lysate.objects.filter(lysate_batch=lysate_batch), form_kwargs={'user': request.user})
	
	return render(request, 'samples/lysates_in_batch.html', { 'lysate_batch_name': lysate_batch_name, 'lysate_batch_form': lysate_batch_form, 'formset': lysates_formset} )
	
# return a spreadsheet version of data for offline editing
@login_required
def lysates_spreadsheet(request):
	lysate_batch_name = request.GET['lysate_batch_name']
	lysate_batch = LysateBatch.objects.get(batch_name=lysate_batch_name)
	
	response = HttpResponse(content_type='text/csv')
	response['Content-Disposition'] = f'attachment; filename="lysate_batch_{lysate_batch_name}.tsv"'

	writer = csv.writer(response, delimiter='\t')
	# header
	writer.writerow(Lysate.spreadsheet_header())
	lysates = Lysate.objects.filter(lysate_batch=lysate_batch)
	for lysate in lysates:
		writer.writerow(lysate.to_spreadsheet_row())
	return response
	
@login_required
def lysates_spreadsheet_upload(request):
	lysate_batch_name = request.GET['lysate_batch_name']
	if request.method == 'POST':
		spreadsheet_form = SpreadsheetForm(request.POST, request.FILES)
		print(f'lysates spreadsheet {lysate_batch_name}')
		if spreadsheet_form.is_valid():
			spreadsheet = request.FILES.get('spreadsheet')
			lysate_batch = LysateBatch.objects.get(batch_name=lysate_batch_name)
			lysate_batch.lysates_from_spreadsheet(spreadsheet, request.user)
			message = 'Values updated'
	else:
		spreadsheet_form = SpreadsheetForm()
		message = ''
	return render(request, 'samples/spreadsheet_upload.html', { 'title': f'Lysates for {lysate_batch_name}', 'form': spreadsheet_form, 'message': message} )

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

@login_required
def lysate_batch_plate_layout(request):
	try:
		lysate_batch_name = request.GET['lysate_batch_name']
	except:
		lysate_batch_name = request.POST['lysate_batch_name']
	lysate_batch = LysateBatch.objects.get(batch_name=lysate_batch_name)
	
	if request.method == 'POST' and request.is_ajax():
		# JSON for a well plate layout
		#print(request.body)
		layout = request.POST['layout']
		objects_map = json.loads(layout)
		#print(objects_map)
		# Cannot have more than one powder per well
		duplicate_error_message = duplicate_positions_check(objects_map)
		if duplicate_error_message is not None:
			return HttpResponseBadRequest(duplicate_error_message)
		# propagate changes to database
		update_db_layout(request.user, objects_map, LysateBatchLayout.objects.filter(lysate_batch=lysate_batch), 'powder_sample', 'powder_sample_id')
		#print('ajax submission')
	elif request.method == 'POST':
		print('POST {lysate_batch_name}')
		raise ValueError('unexpected')
		
	layout_elements = LysateBatchLayout.objects.filter(lysate_batch=lysate_batch).select_related('powder_sample').select_related('control_type')
		
	objects_map = layout_objects_map_for_rendering(layout_elements, 'powder_sample', 'powder_sample_id')
		
	return render(request, 'samples/generic_layout.html', { 'layout_title': 'Powder Sample Layout For Lysate Batch', 'layout_name': lysate_batch_name, 'rows':PLATE_ROWS, 'columns':WELL_PLATE_COLUMNS, 'objects_map': objects_map, 'allow_layout_modifications': (lysate_batch.status == lysate_batch.OPEN) } )

@login_required
def lost_powder(request):
	page_number = request.GET.get('page', 1)
	page_size = request.GET.get('page_size', 25)
	whole_queue = LysateBatchLayout.objects.filter(lysate_batch=None).order_by('-modification_timestamp')
	paginator = Paginator(whole_queue, page_size)
	page_obj = paginator.get_page(page_number)
	page_obj.ordered = True
		
	if request.method == 'POST':
		formset = LostPowderFormset(request.POST, form_kwargs={'user': request.user})
		
		if formset.is_valid():
			formset.save()
		
	elif request.method == 'GET':
		formset = LostPowderFormset(queryset=page_obj, form_kwargs={'user': request.user})
	return render(request, 'samples/generic_formset.html', { 'title': 'Lost Powder', 'page_obj': page_obj, 'formset': formset, 'submit_button_text': 'Update lost powder' } )
	
@login_required
def lysate_batch_to_extract_batch(request):
	lysate_batch_name = request.GET['lysate_batch_name']
	lysate_batch = LysateBatch.objects.get(batch_name=lysate_batch_name)
	if request.method == 'POST':
		form = LysateBatchToExtractBatchForm(request.POST)
		if form.is_valid():
			extract_batch_name = form.cleaned_data['extract_batch_name']
			lysate_batch.create_extract_batch(extract_batch_name, request.user)
			return redirect(f'{reverse("extract_batch_assign_lysate")}?extract_batch_name={extract_batch_name}')
	elif request.method == 'GET':
		form = LysateBatchToExtractBatchForm()
		# Set name for first extraction batch. Duplicates will prompt for new name and need to be set manually. 
		form.initial['extract_batch_name'] = f'{lysate_batch_name.rsplit("_")[0]}_RE'
		
	return render(request, 'samples/batch_transition.html', { 'form': form, 
						'source_batch_name': lysate_batch_name,
						'source_batch_type': 'Lysate Batch',
						'new_batch_type': 'Extract Batch'
						} )
	
@login_required
def extract_batch(request):
	if request.method == 'POST':
		extract_batch_form = ExtractionBatchForm(request.POST, user=request.user)
		if extract_batch_form.is_valid():
			extract_batch_instance = extract_batch_form.save(commit=False)
			if not ExtractionBatch.objects.filter(pk=extract_batch_instance.pk).exists():
				if extract_batch_instance.technician_fk == None:
					wetlab_staff = WetLabStaff.objects.get(login_user=request.user)
					extract_batch_instance.technician_fk = wetlab_staff
					extract_batch_instance.technician = wetlab_staff.initials()
			extract_batch_instance.save()
		
	elif request.method == 'GET':
		extract_batch_form = ExtractionBatchForm(user=request.user)
	
	extract_batches = ExtractionBatch.objects.all()
	# open can have new samples assigned
	return render(request, 'samples/extract_batch.html', { 'extract_batch_form': extract_batch_form, 'extract_batches': extract_batches } )
	
@login_required
def extract_batch_assign_lysate(request):
	extract_batch_name = request.GET['extract_batch_name']
	extract_batch = ExtractionBatch.objects.get(batch_name=extract_batch_name)
	if request.method == 'POST':
		extract_batch_form = ExtractionBatchForm(request.POST, instance=extract_batch, user=request.user)
		if extract_batch_form.is_valid():
			print('valid extract_batch form')
			extract_batch_form.save()
			
			# iterate through the checkboxes and change states
			ticked_checkboxes = request.POST.getlist('lysate_checkboxes[]')
			# tickbox name is lysate object id (int)
			assign_lysates_to_extract_batch(extract_batch, ticked_checkboxes, request.user)
			
			if extract_batch.status == extract_batch.EXTRACTED:
				extract_batch.create_extracts(request.user)
				return redirect(f'{reverse("extracts_in_batch")}?extract_batch_name={extract_batch_name}')
		
	elif request.method == 'GET':
		extract_batch_form = ExtractionBatchForm(instance=extract_batch, user=request.user)
		
	existing_controls = ExtractionBatchLayout.objects.filter(extract_batch=extract_batch, control_type__isnull=False)
	
	already_selected_lysates = ExtractionBatchLayout.objects.filter(extract_batch=extract_batch, control_type=None).values_list('lysate', flat=True)
	
	lysates = Lysate.objects.annotate(num_assignments=Count('extractionbatchlayout')).annotate(assigned_to_extract_batch=Count('extractionbatchlayout', filter=Q(extractionbatchlayout__extract_batch=extract_batch))).filter(
		Q(id__in=already_selected_lysates)
	)
	
	assigned_lysates_count = lysates.count()
	# count wells
	occupied_well_count, num_non_control_assignments = occupied_wells(ExtractionBatchLayout.objects.filter(extract_batch=extract_batch))
	
	return render(request, 'samples/extract_batch_assign_lysate.html', { 'extract_batch_name': extract_batch_name, 'lysates': lysates, 'assigned_lysates_count': assigned_lysates_count, 'control_count': len(existing_controls), 'num_assignments': num_non_control_assignments, 'occupied_wells': occupied_well_count, 'form': extract_batch_form  } )
	
# allow adding any lysate to this batch, free form
@login_required
def extract_batch_add_lysate(request):
	pass

@login_required
def extract_batch_layout(request):
	try:
		extract_batch_name = request.GET['extract_batch_name']
	except:
		extract_batch_name = request.POST['extract_batch_name']
	extract_batch = ExtractionBatch.objects.get(batch_name=extract_batch_name)
	layout_element_queryset = ExtractionBatchLayout.objects.filter(extract_batch=extract_batch)
		
	if request.method == 'POST' and request.is_ajax():
		# JSON for a well plate layout
		#print(request.body)
		layout = request.POST['layout']
		objects_map = json.loads(layout)
		#print(objects_map)
		# Cannot have more than one powder per well
		duplicate_error_message = duplicate_positions_check(objects_map)
		if duplicate_error_message is not None:
			return HttpResponseBadRequest(duplicate_error_message)
		# propagate changes to database
		update_db_layout(request.user, objects_map, ExtractionBatchLayout.objects.filter(extract_batch=extract_batch), 'lysate', 'lysate_id')
	elif request.method == 'POST':
		print('POST {extract_batch_name}')
		raise ValueError('unexpected')
		
	layout_elements = ExtractionBatchLayout.objects.filter(extract_batch=extract_batch).select_related('lysate').select_related('control_type')
		
	objects_map = layout_objects_map_for_rendering(layout_elements, 'lysate', 'lysate_id')
		
	return render(request, 'samples/generic_layout.html', { 'layout_title': 'Lysate Layout For Extract Batch', 'layout_name': extract_batch_name, 'rows':PLATE_ROWS, 'columns':WELL_PLATE_COLUMNS, 'objects_map': objects_map, 'allow_layout_modifications': (extract_batch.status == extract_batch.OPEN)  } )
	
@login_required
def extracts_in_batch(request):
	extract_batch_name = request.GET['extract_batch_name']
	extract_batch = ExtractionBatch.objects.get(batch_name=extract_batch_name)
	
	if request.method == 'POST':
		extract_batch_form = ExtractionBatchForm(request.POST, instance=extract_batch, user=request.user)
		extracts_formset = ExtractFormset(request.POST, request.FILES, form_kwargs={'user': request.user})
		
		if extract_batch_form.is_valid():
			extract_batch_form.save()
		if extracts_formset.is_valid():
			extracts_formset.save()
		if extract_batch_form.is_valid() and extracts_formset.is_valid():
			if extract_batch.status == extract_batch.OPEN:
				return redirect(f'{reverse("extract_batch_assign_lysate")}?extract_batch_name={extract_batch_name}')
		
	elif request.method == 'GET':
		extract_batch_form = ExtractionBatchForm(instance=extract_batch, user=request.user)
		extracts_formset = ExtractFormset(queryset=Extract.objects.filter(extract_batch=extract_batch), form_kwargs={'user': request.user})
	
	return render(request, 'samples/extracts_in_batch.html', { 'extract_batch_name': extract_batch_name, 'extract_batch_form': extract_batch_form, 'formset': extracts_formset} )
	
# return a spreadsheet version of data for offline editing
@login_required
def extracts_spreadsheet(request):
	extract_batch_name = request.GET['extract_batch_name']
	extract_batch = ExtractionBatch.objects.get(batch_name=extract_batch_name)
	
	response = HttpResponse(content_type='text/csv')
	response['Content-Disposition'] = f'attachment; filename="extract_batch_{extract_batch_name}.tsv"'

	writer = csv.writer(response, delimiter='\t')
	# header
	writer.writerow(Extract.spreadsheet_header())
	extracts = Extract.objects.filter(extract_batch=extract_batch)
	for extract in extracts:
		writer.writerow(extract.to_spreadsheet_row())
	return response

@login_required
def extracts_spreadsheet_upload(request):
	extract_batch_name = request.GET['extract_batch_name']
	if request.method == 'POST':
		spreadsheet_form = SpreadsheetForm(request.POST, request.FILES)
		print(f'extracts spreadsheet {extract_batch_name}')
		if spreadsheet_form.is_valid():
			spreadsheet = request.FILES.get('spreadsheet')
			extract_batch = ExtractionBatch.objects.get(batch_name=extract_batch_name)
			extract_batch.extracts_from_spreadsheet(spreadsheet, request.user)
			message = 'Values updated'
	else:
		spreadsheet_form = SpreadsheetForm()
		message = ''
	return render(request, 'samples/spreadsheet_upload.html', { 'title': f'Extracts for {extract_batch_name}', 'form': spreadsheet_form, 'message': message} )
	
@login_required
def extract_batch_to_library_batch(request):
	extract_batch_name = request.GET['extract_batch_name']
	extract_batch = ExtractionBatch.objects.get(batch_name=extract_batch_name)
	if request.method == 'POST':
		form = ExtractBatchToLibraryBatchForm(request.POST)
		if form.is_valid():
			library_batch_name = form.cleaned_data['library_batch_name']
			extract_batch.create_library_batch(library_batch_name, request.user)
			return redirect(f'{reverse("library_batch_assign_extract")}?library_batch_name={library_batch_name}')
	elif request.method == 'GET':
		form = ExtractBatchToLibraryBatchForm()
		# Set name for first extraction batch. Duplicates will prompt for new name and need to be set manually. 
		# TODO this defaults to double-stranded but should also handle single-stranded
		form.initial['library_batch_name'] = f'{extract_batch_name.rsplit("_")[0]}_DS'
		
	return render(request, 'samples/batch_transition.html', { 'form': form, 
						'source_batch_name': extract_batch_name,
						'source_batch_type': 'Extract Batch',
						'new_batch_type': 'Library Batch'
						} )

@login_required
def lost_lysate(request):
	page_number = request.GET.get('page', 1)
	page_size = request.GET.get('page_size', 25)
	whole_queue = ExtractionBatchLayout.objects.filter(extract_batch=None).order_by('-modification_timestamp')
	paginator = Paginator(whole_queue, page_size)
	page_obj = paginator.get_page(page_number)
	page_obj.ordered = True
		
	if request.method == 'POST':
		formset = LostLysateFormset(request.POST, form_kwargs={'user': request.user})
		
		if formset.is_valid():
			formset.save()
		
	elif request.method == 'GET':
		formset = LostLysateFormset(queryset=page_obj, form_kwargs={'user': request.user})
	return render(request, 'samples/generic_formset.html', { 'title': 'Lost Lysate', 'page_obj': page_obj, 'formset': formset, 'submit_button_text': 'Update lost lysate' } )
	
@login_required
def library_batches(request):
	if request.method == 'POST':
		form = LibraryBatchForm(request.POST, user=request.user)
		if form.is_valid():
			form.save()
	elif request.method == 'GET':
		form = LibraryBatchForm(user=request.user)
		
	library_batches_queryset = LibraryBatch.objects.all()
	return render(request, 'samples/library_batches.html', { 'form': form, 'library_batches': library_batches_queryset } )
	
@login_required
def library_batch_assign_extract(request):
	library_batch_name = request.GET['library_batch_name']
	library_batch = LibraryBatch.objects.get(name=library_batch_name)
	if request.method == 'POST':
		library_batch_form = LibraryBatchForm(request.POST, instance=library_batch, user=request.user)
		if library_batch_form.is_valid():
			print('valid library_batch form')
			library_batch_form.save()
			
			# iterate through the checkboxes and change states
			ticked_checkboxes = request.POST.getlist('extract_checkboxes[]')
			# tickbox name is extract object id (int)
			library_batch.assign_extracts_to_library_batch(ticked_checkboxes, request.user)
			
			if library_batch.status == library_batch.LIBRARIED:
				library_batch.create_libraries(request.user)
				return redirect(f'{reverse("libraries_in_batch")}?library_batch_name={library_batch_name}')
		
	elif request.method == 'GET':
		library_batch_form = LibraryBatchForm(instance=library_batch, user=request.user)
		
	existing_controls = LibraryBatchLayout.objects.filter(library_batch=library_batch, control_type__isnull=False)
	
	already_selected_extracts = LibraryBatchLayout.objects.filter(library_batch=library_batch, control_type=None).values_list('extract', flat=True)
	
	extracts = Extract.objects.annotate(num_assignments=Count('librarybatchlayout')).annotate(assigned_to_library_batch=Count('librarybatchlayout', filter=Q(librarybatchlayout__library_batch=library_batch))).filter(
		Q(id__in=already_selected_extracts)
	)
	
	assigned_extracts_count = extracts.count()
	# count wells
	occupied_well_count, num_non_control_assignments = occupied_wells(LibraryBatchLayout.objects.filter(library_batch=library_batch))
	
	return render(request, 'samples/library_batch_assign_extract.html', { 'library_batch_name': library_batch_name, 'extracts': extracts, 'assigned_extracts_count': assigned_extracts_count, 'control_count': len(existing_controls), 'num_assignments': num_non_control_assignments, 'occupied_wells': occupied_well_count, 'form': library_batch_form  } )
	
# return comma-delimited spreadsheet version of barcodes for robot
@login_required
def library_batch_barcodes_spreadsheet(request):
	library_batch_name = request.GET['library_batch_name']
	library_batch = LibraryBatch.objects.get(name=library_batch_name)
	
	response = HttpResponse(content_type='text/csv')
	response['Content-Disposition'] = f'attachment; filename="library_batch_{library_batch_name}_barcodes.tsv"'

	writer = csv.writer(response, delimiter=',')
	# header
	writer.writerow(['Source', 'Destination', 'Amount'])
	robot_layout = library_batch.get_robot_layout()
	#print(robot_layout)
	for entry in robot_layout:
		writer.writerow(entry)
	return response

@login_required
def library_batch_layout(request):
	try:
		library_batch_name = request.GET['library_batch_name']
	except:
		library_batch_name = request.POST['library_batch_name']
	library_batch = LibraryBatch.objects.get(name=library_batch_name)
	layout_element_queryset = LibraryBatchLayout.objects.filter(library_batch=library_batch)
		
	if request.method == 'POST' and request.is_ajax():
		# JSON for a well plate layout
		#print(request.body)
		layout = request.POST['layout']
		objects_map = json.loads(layout)
		#print(objects_map)
		# Cannot have more than one powder per well
		duplicate_error_message = duplicate_positions_check(objects_map)
		if duplicate_error_message is not None:
			return HttpResponseBadRequest(duplicate_error_message)
		# propagate changes to database
		update_db_layout(request.user, objects_map, LibraryBatchLayout.objects.filter(library_batch=library_batch), 'extract', 'extract_id')
	elif request.method == 'POST':
		print('POST {library_batch_name}')
		raise ValueError('unexpected')
		
	layout_elements = LibraryBatchLayout.objects.filter(library_batch=library_batch).select_related('extract').select_related('control_type')
		
	objects_map = layout_objects_map_for_rendering(layout_elements, 'extract', 'extract_id')
		
	return render(request, 'samples/generic_layout.html', { 'layout_title': 'Extract Layout For Library Batch', 'layout_name': library_batch_name, 'rows':PLATE_ROWS, 'columns':WELL_PLATE_COLUMNS, 'objects_map': objects_map, 'allow_layout_modifications': (library_batch.status == library_batch.OPEN) } )
	
@login_required
def libraries_in_batch(request):
	library_batch_name = request.GET['library_batch_name']
	library_batch = LibraryBatch.objects.get(name=library_batch_name)
	
	if request.method == 'POST':
		library_batch_form = LibraryBatchForm(request.POST, instance=library_batch, user=request.user)
		libraries_formset = LibraryFormset(request.POST, request.FILES, form_kwargs={'user': request.user})
		
		if library_batch_form.is_valid():
			library_batch_form.save()
		if libraries_formset.is_valid():
			libraries_formset.save()
		if library_batch_form.is_valid() and libraries_formset.is_valid():
			if library_batch.status == library_batch.OPEN:
				return redirect(f'{reverse("library_batch_assign_extract")}?library_batch_name={library_batch_name}')
		
	elif request.method == 'GET':
		library_batch_form = LibraryBatchForm(instance=library_batch, user=request.user)
		libraries_formset = LibraryFormset(queryset=Library.objects.filter(library_batch=library_batch), form_kwargs={'user': request.user})
	
	return render(request, 'samples/libraries_in_batch.html', { 'library_batch_name': library_batch_name, 'library_batch_form': library_batch_form, 'formset': libraries_formset} )
	
# return a spreadsheet version of data for offline editing
@login_required
def libraries_spreadsheet(request):
	library_batch_name = request.GET['library_batch_name']
	library_batch = LibraryBatch.objects.get(name=library_batch_name)
	
	response = HttpResponse(content_type='text/csv')
	response['Content-Disposition'] = f'attachment; filename="library_batch_{library_batch_name}.tsv"'

	writer = csv.writer(response, delimiter='\t')
	# header
	writer.writerow(Library.spreadsheet_header())
	libraries = Library.objects.filter(library_batch=library_batch)
	for library in libraries:
		writer.writerow(library.to_spreadsheet_row())
	return response

@login_required
def libraries_spreadsheet_upload(request):
	library_batch_name = request.GET['library_batch_name']
	if request.method == 'POST':
		spreadsheet_form = SpreadsheetForm(request.POST, request.FILES)
		print(f'libraries spreadsheet {library_batch_name}')
		if spreadsheet_form.is_valid():
			spreadsheet = request.FILES.get('spreadsheet')
			library_batch = LibraryBatch.objects.get(name=library_batch_name)
			library_batch.libraries_from_spreadsheet(spreadsheet, request.user)
			message = 'Values updated'
	else:
		spreadsheet_form = SpreadsheetForm()
		message = ''
	return render(request, 'samples/spreadsheet_upload.html', { 'title': f'Librarie for {library_batch_name}', 'form': spreadsheet_form, 'message': message} )

@login_required
def storage_all(request):
	page_number = request.GET.get('page', 1)
	page_size = request.GET.get('page_size', 25)
	whole_queue = Storage.objects.all().order_by('-id')
	paginator = Paginator(whole_queue, page_size)
	page_obj = paginator.get_page(page_number)
	page_obj.ordered = True
		
	if request.method == 'POST':
		formset =StorageFormset(request.POST, form_kwargs={'user': request.user})
		
		if formset.is_valid():
			formset.save()
		
	elif request.method == 'GET':
		formset = StorageFormset(queryset=page_obj, form_kwargs={'user': request.user})
	return render(request, 'samples/generic_formset.html', { 'title': 'Storage', 'page_obj': page_obj, 'formset': formset, 'submit_button_text': 'Update' } ) 
		
def logout_user(request):
	return logout_then_login(request)

@login_required
def password_changed(request):
	return render(request, 'samples/password_changed.html', {} )
