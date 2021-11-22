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
from samples.models import Results, Library, Sample, PowderBatch, WetLabStaff, PowderSample, ControlType, ControlSet, ControlLayout, ExtractionProtocol, LysateBatch, SamplePrepQueue, PLATE_ROWS, LysateBatchLayout, ExtractionBatch, ExtractionBatchLayout, Lysate, LibraryBatch, LibraryBatchLayout, Extract, CaptureOrShotgunPlate, CaptureLayout, Storage
from .forms import *
from sequencing_run.models import MTAnalysis

from .powder_samples import new_reich_lab_powder_sample, assign_prep_queue_entries_to_powder_batch
from .layout import duplicate_positions_check, update_db_layout,  layout_objects_map_for_rendering, occupied_wells, layout_and_content_lists, PLATE_WELL_COUNT

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
def sample_prep_queue_spreadsheet(request):
	sample_queue = SamplePrepQueue.objects.filter(Q(powder_batch=None)).select_related('sample').select_related('sample_prep_protocol').order_by('priority')
	
	response = HttpResponse(content_type='text/csv')
	response['Content-Disposition'] = f'attachment; filename="sample_prep_queue.txt"'

	writer = csv.writer(response, delimiter='\t')
	# header
	writer.writerow(SamplePrepQueue.spreadsheet_header())
	for x in sample_queue:
		writer.writerow(x.to_spreadsheet_row())
	return response

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
					).order_by('-id')
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
			
			if powder_batch.status not in [powder_batch.STOP, powder_batch.OPEN]:
				return redirect(f'{reverse("powder_samples")}?powder_batch={powder_batch_name}')
		
	elif request.method == 'GET':
		form = PowderBatchForm(user=request.user, initial={'name': powder_batch_name, 'date': powder_batch.date, 'status': powder_batch.status, 'notes': powder_batch.notes}, instance=powder_batch)
	
	# show samples assigned to this powder batch and unassigned samples
	sample_queue = SamplePrepQueue.objects.filter(Q(powder_batch=None, powder_sample=None) | Q(powder_batch=powder_batch)).select_related('sample').select_related('sample_prep_protocol').order_by('priority')
	# count for feedback
	num_sample_prep = SamplePrepQueue.objects.filter(powder_batch=powder_batch).count()
	num_powder_samples = PowderSample.objects.filter(powder_batch=powder_batch).count()
	return render(request, 'samples/powder_batch_assign_sample.html', { 'queued_samples': sample_queue, 'powder_batch_name': powder_batch_name, 'form': form, 'num_sample_prep': num_sample_prep, 'num_powder_samples': num_powder_samples } )
	
@login_required
def powder_batch_delete(request):
	powder_batch_name = request.GET['batch_name']
	try:
		powder_batch = PowderBatch.objects.get(name=powder_batch_name)
		powder_batch_form = PowderBatchForm(instance=powder_batch, user=request.user)
		powder_batch_form.disable_fields()
	except PowderBatch.DoesNotExist:
		return HttpResponse(f'{powder_batch_name} no longer exists.')
	
	if request.method == 'POST':
		print(f'request to delete {powder_batch_name}')
		powder_batch.delete()
		return redirect(f'{reverse("powder_batches")}')
		
	return render(request, 'samples/delete_batch.html', {'form': powder_batch_form, 'batch_type': 'Powder Batch', 'batch_name': powder_batch_name, 'cancel_link': 'powder_batch'})

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
		if powder_batch_form.is_valid() and (powder_batch.status in [powder_batch.OPEN, powder_batch.STOP]):
				return redirect(f'{reverse("powder_batch_assign_samples")}?name={powder_batch_name}')
		
	elif request.method == 'GET':
		powder_batch_form = PowderBatchForm(initial={'name': powder_batch_name, 'date': powder_batch.date, 'status': powder_batch.status, 'notes': powder_batch.notes}, instance=powder_batch, user=request.user)
		powder_batch_sample_formset = PowderSampleFormset(queryset=PowderSample.objects.filter(powder_batch=powder_batch).order_by('sample__reich_lab_id'), form_kwargs={'user': request.user})
	
	# open can have new samples assigned
	return render(request, 'samples/powder_samples.html', { 'powder_batch_name': powder_batch_name, 'powder_batch_form': powder_batch_form, 'formset': powder_batch_sample_formset} )
	
# return a spreadsheet version of data for offline editing
@login_required
def powder_samples_spreadsheet(request):
	powder_batch_name = request.GET['powder_batch_name']
	powder_batch = PowderBatch.objects.get(name=powder_batch_name)
	
	response = HttpResponse(content_type='text/csv')
	response['Content-Disposition'] = f'attachment; filename="powder_batch_{powder_batch_name}.txt"'

	writer = csv.writer(response, delimiter='\t')
	# header
	writer.writerow(PowderSample.spreadsheet_header())
	powder_samples = PowderSample.objects.filter(powder_batch=powder_batch).order_by('sample__reich_lab_id')
	for powder_sample in powder_samples:
		writer.writerow(powder_sample.to_spreadsheet_row())
	return response
	
@login_required
def powder_samples_spreadsheet_upload(request):
	powder_batch_name = request.GET['powder_batch_name']
	if request.method == 'POST':
		powder_batch = PowderBatch.objects.get(name=powder_batch_name)
		spreadsheet_form = SpreadsheetForm(request.POST, request.FILES)
		print(f'powder sample spreadsheet {powder_batch_name}')
		if spreadsheet_form.is_valid():
			spreadsheet = request.FILES.get('spreadsheet')
			powder_batch.powder_samples_from_spreadsheet(spreadsheet, request.user)
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
		extraction_protocol_formset = ExtractionProtocolFormset(queryset=ExtractionProtocol.objects.all().order_by('-end_date'), form_kwargs={'user': request.user})
	
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
	
	lysate_batches = LysateBatch.objects.all().order_by('-id')
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
			
			ticked_checkboxes = request.POST.getlist('powder_sample_checkboxes[]')
			layout_ids, powder_sample_ids =layout_and_content_lists(ticked_checkboxes)
			# validate number of selections
			total_wells = lysate_batch.num_controls() + len(layout_ids) + len(powder_sample_ids)
			if total_wells > PLATE_WELL_COUNT:
				return HttpResponse(f'Too many powders and controls {total_wells}')
			
			lysate_batch.restrict_layout_elements(layout_ids)
			lysate_batch.assign_powder_samples(powder_sample_ids, request.user)
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
			lysate_batch_form = LysateBatchForm(instance=lysate_batch, user=request.user)
		
	elif request.method == 'GET':
		lysate_batch_form = LysateBatchForm(instance=lysate_batch, user=request.user)
		
	existing_controls = LysateBatchLayout.objects.filter(lysate_batch=lysate_batch, control_type__isnull=False)
	
	'''
	already_selected_powder_sample_ids = LysateBatchLayout.objects.filter(lysate_batch=lysate_batch, control_type=None).values_list('powder_sample', flat=True)
	powder_samples_already_selected = PowderSample.objects.annotate(num_assignments=Count('lysatebatchlayout')).annotate(assigned_to_lysate_batch=Count('lysatebatchlayout', filter=Q(lysatebatchlayout__lysate_batch=lysate_batch))).filter(
		Q(id__in=already_selected_powder_sample_ids)
	)
	'''
	layout_powder_samples_already_selected = LysateBatchLayout.objects.filter(lysate_batch=lysate_batch, control_type=None).order_by('row', 'column').select_related('powder_sample')
	powder_samples_unselected = PowderSample.objects.annotate(num_assignments=Count('lysatebatchlayout')).annotate(assigned_to_lysate_batch=Count('lysatebatchlayout', filter=Q(lysatebatchlayout__lysate_batch=lysate_batch))).filter(
		Q(num_assignments=0) &
		(Q(powder_batch__status=PowderBatch.READY_FOR_PLATE)
		| (Q(powder_batch=None) & ~Q(powder_sample_id__endswith='NP')))# powder samples directly from collaborators will not have powder batch. Exclude controls. 
	).order_by('powder_batch', 'sample__reich_lab_id')
	#powder_samples = powder_samples_already_selected.union(powder_samples_unselected).order_by('id')
	
	powder_samples = {}
	for layout_element in layout_powder_samples_already_selected:
		powder_samples[layout_element.powder_sample] = True
	assigned_powder_samples_count = len(powder_samples)
	# count wells
	occupied_well_count, num_non_control_assignments = occupied_wells(LysateBatchLayout.objects.filter(lysate_batch=lysate_batch))
	
	return render(request, 'samples/lysate_batch_assign_powder.html', { 'lysate_batch_name': lysate_batch_name, 'assigned_powder_samples': layout_powder_samples_already_selected, 'powder_samples': powder_samples_unselected, 'assigned_powder_samples_count': assigned_powder_samples_count, 'control_count': len(existing_controls), 'num_assignments': num_non_control_assignments, 'occupied_wells': occupied_well_count, 'form': lysate_batch_form  } )
	
@login_required
def lysate_batch_delete(request):
	lysate_batch_name = request.GET['batch_name']
	try:
		lysate_batch = LysateBatch.objects.get(batch_name=lysate_batch_name)
		lysate_batch_form = LysateBatchForm(instance=lysate_batch, user=request.user)
		lysate_batch_form.disable_fields()
	except LysateBatch.DoesNotExist:
		return HttpResponse(f'{lysate_batch_name} no longer exists.')
	
	if request.method == 'POST':
		print(f'request to delete {lysate_batch_name}')
		lysate_batch.delete()
		return redirect(f'{reverse("lysate_batch")}')
		
	return render(request, 'samples/delete_batch.html', {'form': lysate_batch_form, 'batch_type': 'Lysate Batch', 'batch_name': lysate_batch_name, 'cancel_link': 'lysate_batch'})
	
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
		lysates_formset = LysateFormset(queryset=Lysate.objects.filter(lysate_batch=lysate_batch).order_by('lysatebatchlayout__column', 'lysatebatchlayout__row'), form_kwargs={'user': request.user})
	
	return render(request, 'samples/lysates_in_batch.html', { 'lysate_batch_name': lysate_batch_name, 'lysate_batch_form': lysate_batch_form, 'formset': lysates_formset} )
	
# return a spreadsheet version of data for offline editing
@login_required
def lysates_spreadsheet(request):
	lysate_batch_name = request.GET['lysate_batch_name']
	lysate_batch = LysateBatch.objects.get(batch_name=lysate_batch_name)
	
	response = HttpResponse(content_type='text/csv')
	response['Content-Disposition'] = f'attachment; filename="lysate_batch_{lysate_batch_name}.txt"'

	writer = csv.writer(response, delimiter='\t')
	# header
	writer.writerow(LysateBatchLayout.spreadsheet_header())
	lysates = LysateBatchLayout.objects.filter(lysate_batch=lysate_batch).order_by('column', 'row')
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
	
	extract_batches = ExtractionBatch.objects.all().order_by('-id')
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
			layout_ids, lysate_ids =layout_and_content_lists(ticked_checkboxes)
			# tickbox name is lysate object id (int)
			extract_batch.restrict_layout_elements(layout_ids)
			# extra lysates are not currently listed, so there are none to add
			
			if extract_batch.status == extract_batch.EXTRACTED:
				extract_batch.create_extracts(request.user)
				return redirect(f'{reverse("extracts_in_batch")}?extract_batch_name={extract_batch_name}')
		
	elif request.method == 'GET':
		extract_batch_form = ExtractionBatchForm(instance=extract_batch, user=request.user)
		
	existing_controls = ExtractionBatchLayout.objects.filter(extract_batch=extract_batch, control_type__isnull=False)
	
	already_selected_lysate_layout_elements = ExtractionBatchLayout.objects.filter(extract_batch=extract_batch, control_type=None).order_by('column', 'row')
	
	# count distinct lysates
	lysates = {}
	for layout_element in already_selected_lysate_layout_elements:
		lysates[layout_element.lysate] = True
	assigned_lysates_count = len(lysates)
	# count wells
	occupied_well_count, num_non_control_assignments = occupied_wells(ExtractionBatchLayout.objects.filter(extract_batch=extract_batch))
	
	return render(request, 'samples/extract_batch_assign_lysate.html', { 'extract_batch_name': extract_batch_name, 'assigned_lysates': already_selected_lysate_layout_elements, 'assigned_lysates_count': assigned_lysates_count, 'control_count': len(existing_controls), 'num_assignments': num_non_control_assignments, 'occupied_wells': occupied_well_count, 'form': extract_batch_form  } )
	
@login_required
def extract_batch_delete(request):
	extract_batch_name = request.GET['batch_name']
	try:
		extract_batch = ExtractionBatch.objects.get(batch_name=extract_batch_name)
		extract_batch_form = ExtractionBatchForm(instance=extract_batch, user=request.user)
		extract_batch_form.disable_fields()
	except ExtractionBatch.DoesNotExist:
		return HttpResponse(f'{extract_batch_name} no longer exists.')
	
	if request.method == 'POST':
		print(f'request to delete {extract_batch_name}')
		extract_batch.delete()
		return redirect(f'{reverse("extract_batch")}')
		
	return render(request, 'samples/delete_batch.html', {'form': extract_batch_form, 'batch_type': 'Extract Batch', 'batch_name': extract_batch_name, 'cancel_link': 'extract_batch'})
	
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
		extracts_formset = ExtractFormset(queryset=Extract.objects.filter(extract_batch=extract_batch).order_by('extractionbatchlayout__column', 'extractionbatchlayout__row'), form_kwargs={'user': request.user})
	
	return render(request, 'samples/extracts_in_batch.html', { 'extract_batch_name': extract_batch_name, 'extract_batch_form': extract_batch_form, 'formset': extracts_formset} )
	
# return a spreadsheet version of data for offline editing
@login_required
def extracts_spreadsheet(request):
	extract_batch_name = request.GET['extract_batch_name']
	extract_batch = ExtractionBatch.objects.get(batch_name=extract_batch_name)
	
	response = HttpResponse(content_type='text/csv')
	response['Content-Disposition'] = f'attachment; filename="extract_batch_{extract_batch_name}.txt"'

	writer = csv.writer(response, delimiter='\t')
	# header
	writer.writerow(ExtractionBatchLayout.spreadsheet_header())
	extracts = ExtractionBatchLayout.objects.filter(extract_batch=extract_batch).order_by('column', 'row')
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
def library_protocols(request):
	if request.method == 'POST':
		form = LibraryProtocolForm(request.POST, user=request.user)
		if form.is_valid():
			form.save()
	elif request.method == 'GET':
		form = LibraryProtocolForm(user=request.user)
		
	library_protocols_queryset = LibraryProtocol.objects.all().order_by('-id')
	return render(request, 'samples/library_protocols.html', { 'form': form, 'library_protocols': library_protocols_queryset } )
	
@login_required
def library_protocol(request):
	library_protocol_name = request.GET['library_protocol_name']
	if request.method == 'POST':
		form = LibraryProtocolForm(request.POST, user=request.user)
		if form.is_valid():
			form.save()
	elif request.method == 'GET':
		library_protocol = LibraryProtocol.objects.get(name=library_protocol_name)
		form = LibraryProtocolForm(user=request.user, instance=library_protocol)
		
	return render(request, 'samples/generic_form.html', { 'title': f'Library Protocol {library_protocol_name}', 'form': form, } )
	
@login_required
def library_batches(request):
	if request.method == 'POST':
		form = LibraryBatchForm(request.POST, user=request.user)
		if form.is_valid():
			form.save()
	elif request.method == 'GET':
		form = LibraryBatchForm(user=request.user)
		
	library_batches_queryset = LibraryBatch.objects.all().order_by('-id')
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
			layout_ids, extract_ids = layout_and_content_lists(ticked_checkboxes)
			library_batch.restrict_layout_elements(layout_ids, request.user)
			
			if library_batch.status == library_batch.LIBRARIED:
				library_batch.create_libraries(request.user)
				return redirect(f'{reverse("libraries_in_batch")}?library_batch_name={library_batch_name}')
		
	elif request.method == 'GET':
		library_batch_form = LibraryBatchForm(instance=library_batch, user=request.user)
		
	existing_controls = LibraryBatchLayout.objects.filter(library_batch=library_batch, control_type__isnull=False).order_by('column', 'row')
	
	already_selected_extract_layout_elements = LibraryBatchLayout.objects.filter(library_batch=library_batch, control_type=None).order_by('column', 'row')
	
	# count distinct extracts
	extracts = {}
	for layout_element in already_selected_extract_layout_elements:
		extracts[layout_element.extract] = True
	assigned_extracts_count = len(extracts)
	
	# count wells
	occupied_well_count, num_non_control_assignments = occupied_wells(LibraryBatchLayout.objects.filter(library_batch=library_batch))
	
	return render(request, 'samples/library_batch_assign_extract.html', { 'library_batch_name': library_batch_name, 'assigned_extracts': already_selected_extract_layout_elements, 'assigned_extracts_count': assigned_extracts_count, 'control_count': len(existing_controls), 'num_assignments': num_non_control_assignments, 'occupied_wells': occupied_well_count, 'form': library_batch_form  } )
	
@login_required
def library_batch_delete(request):
	library_batch_name = request.GET['batch_name']
	try:
		library_batch = LibraryBatch.objects.get(name=library_batch_name)
		library_batch_form = LibraryBatchForm(instance=library_batch, user=request.user)
		library_batch_form.disable_fields()
	except LibraryBatch.DoesNotExist:
		return HttpResponse(f'{library_batch_name} no longer exists.')
	
	if request.method == 'POST':
		print(f'request to delete {library_batch_name}')
		library_batch.delete()
		return redirect(f'{reverse("library_batches")}')
		
	return render(request, 'samples/delete_batch.html', {'form': library_batch_form, 'batch_type': 'Library Batch', 'batch_name': library_batch_name, 'link': 'library_batches'})
	
# return comma-delimited spreadsheet version of barcodes for robot
@login_required
def library_batch_barcodes_spreadsheet(request):
	library_batch_name = request.GET['library_batch_name']
	library_batch = LibraryBatch.objects.get(name=library_batch_name)
	
	response = HttpResponse(content_type='text/csv')
	response['Content-Disposition'] = f'attachment; filename="library_batch_{library_batch_name}_barcodes.csv"'

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
		libraries_formset = LibraryFormset(queryset=Library.objects.filter(library_batch=library_batch).select_related('p5_index', 'p7_index', 'p5_barcode', 'p7_barcode').prefetch_related('librarybatchlayout_set').order_by('librarybatchlayout__column', 'librarybatchlayout__row'), form_kwargs={'user': request.user})
	
	return render(request, 'samples/libraries_in_batch.html', { 'library_batch_name': library_batch_name, 'library_batch_form': library_batch_form, 'formset': libraries_formset} )
	
# return a spreadsheet version of data for offline editing
@login_required
def libraries_spreadsheet(request):
	library_batch_name = request.GET['library_batch_name']
	library_batch = LibraryBatch.objects.get(name=library_batch_name)
	
	response = HttpResponse(content_type='text/csv')
	response['Content-Disposition'] = f'attachment; filename="library_batch_{library_batch_name}.txt"'

	writer = csv.writer(response, delimiter='\t')
	# header
	writer.writerow(LibraryBatchLayout.spreadsheet_header())
	layout_elements = LibraryBatchLayout.objects.filter(library_batch=library_batch).order_by('column', 'row')
	for layout_element in layout_elements:
		writer.writerow(layout_element.to_spreadsheet_row())
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
def library_batch_to_capture_batch(request):
	library_batch_name = request.GET['library_batch_name']
	library_batch = LibraryBatch.objects.get(name=library_batch_name)
	if request.method == 'POST':
		form = LibraryBatchToCaptureBatchForm(request.POST)
		if form.is_valid():
			capture_batch_name = form.cleaned_data['capture_batch_name']
			library_batch.create_capture(capture_batch_name, request.user)
			return redirect(f'{reverse("capture_batch_assign_library")}?capture_batch_name={capture_batch_name}')
	elif request.method == 'GET':
		form = LibraryBatchToCaptureBatchForm()
		# For now, manual only
		form.initial['capture_batch_name'] = f'{library_batch_name.rsplit("_")[0]}'
		
	return render(request, 'samples/batch_transition.html', { 'form': form, 
						'source_batch_name': library_batch_name,
						'source_batch_type': 'Library Batch',
						'new_batch_type': 'Capture or Shotgun Batch'
						} )
	
@login_required
def capture_protocols(request):
	if request.method == 'POST':
		form = CaptureProtocolForm(request.POST, user=request.user)
		if form.is_valid():
			form.save()
	elif request.method == 'GET':
		form = CaptureProtocolForm(user=request.user)
		
	capture_protocols_queryset = CaptureProtocol.objects.all().order_by('-id')
	return render(request, 'samples/capture_protocols.html', { 'form': form, 'capture_protocols': capture_protocols_queryset } )
	
@login_required
def capture_protocol(request):
	capture_protocol_name = request.GET['capture_protocol_name']
	if request.method == 'POST':
		form = CaptureProtocolForm(request.POST, user=request.user)
		if form.is_valid():
			form.save()
	elif request.method == 'GET':
		library_protocol = CaptureProtocol.objects.get(name=capture_protocol_name)
		form = CaptureProtocolForm(user=request.user, instance=library_protocol)
		
	return render(request, 'samples/generic_form.html', { 'title': f'Capture Protocol {library_protocol_name}', 'form': form, } )
	
@login_required
def capture_batches(request):
	if request.method == 'POST':
		form = CaptureBatchForm(request.POST, user=request.user)
		if form.is_valid():
			form.save()
	elif request.method == 'GET':
		form = CaptureBatchForm(user=request.user)
		
	capture_batches_queryset = CaptureOrShotgunPlate.objects.all().order_by('-id')
	return render(request, 'samples/capture_batches.html', { 'form': form, 'capture_batches': capture_batches_queryset } )
	
@login_required
def capture_batch_assign_library(request):
	capture_batch_name = request.GET['capture_batch_name']
	capture_batch = CaptureOrShotgunPlate.objects.get(name=capture_batch_name)
	if request.method == 'POST':
		capture_batch_form = CaptureBatchForm(request.POST, instance=capture_batch, user=request.user)
		if capture_batch_form.is_valid():
			capture_batch_form.save()
			
			if capture_batch.status != capture_batch.STOP:
				# iterate through the checkboxes and change states
				ticked_checkboxes = request.POST.getlist('library_checkboxes[]')
				layout_ids, extract_ids = layout_and_content_lists(ticked_checkboxes)
				capture_batch.restrict_layout_elements(layout_ids, request.user)
			
			if 'assign_plus_indices' in request.POST:
				capture_batch.assign_indices(request.user)
		
	elif request.method == 'GET':
		capture_batch_form = CaptureBatchForm(instance=capture_batch, user=request.user)
		
	existing_controls = CaptureLayout.objects.filter(capture_batch=capture_batch, control_type__isnull=False).order_by('column', 'row')
	
	already_selected_library_layout_elements = CaptureLayout.objects.filter(capture_batch=capture_batch, control_type=None).select_related('library', 'library__p5_barcode', 'library__p7_barcode', 'p5_index', 'p7_index').order_by('column', 'row')
	
	# count distinct libraries
	libraries = {}
	for layout_element in already_selected_library_layout_elements:
		libraries[layout_element.library] = True
	assigned_libraries_count = len(libraries)
	
	# count wells
	occupied_well_count, num_non_control_assignments = occupied_wells(CaptureLayout.objects.filter(capture_batch=capture_batch))
	
	return render(request, 'samples/capture_batch_assign_library.html', { 'capture_batch_name': capture_batch_name, 'capture_batch': capture_batch, 'assigned_libraries': already_selected_library_layout_elements, 'assigned_libraries_count': assigned_libraries_count, 'control_count': len(existing_controls), 'num_assignments': num_non_control_assignments, 'occupied_wells': occupied_well_count, 'form': capture_batch_form  } )
	
@login_required
def captures_in_batch(request):
	capture_batch_name = request.GET['capture_batch_name']
	capture_batch = CaptureOrShotgunPlate.objects.get(name=capture_batch_name)
	
	if request.method == 'POST':
		form = CaptureBatchForm(request.POST, instance=capture_batch, user=request.user)
		captures_formset = CapturedLibraryFormset(request.POST, request.FILES, form_kwargs={'user': request.user})
		
		if form.is_valid():
			form.save()
		if captures_formset.is_valid():
			captures_formset.save()
		if form.is_valid() and capture_batch.status == capture_batch.OPEN:
				return redirect(f'{reverse("capture_batch_assign_library")}?capture_batch_name={capture_batch_name}')
		
	elif request.method == 'GET':
		form = CaptureBatchForm(instance=capture_batch, user=request.user)
		captures_formset = CapturedLibraryFormset(queryset=CaptureLayout.objects.filter(capture_batch=capture_batch).order_by('column', 'row'), form_kwargs={'user': request.user})
	
	return render(request, 'samples/captures_in_batch.html', { 'capture_batch_name': capture_batch_name, 'form': form, 'formset': captures_formset} )
	
@login_required
def capture_batch_layout(request):
	try:
		capture_batch_name = request.GET['capture_batch_name']
	except:
		capture_batch_name = request.POST['capture_batch_name']
	capture_batch = CaptureOrShotgunPlate.objects.get(name=capture_batch_name)
	layout_element_queryset = CaptureLayout.objects.filter(capture_batch=capture_batch)
		
	if request.method == 'POST' and request.is_ajax():
		# JSON for a well plate layout
		#print(request.body)
		layout = request.POST['layout']
		objects_map = json.loads(layout)
		#print(objects_map)
		# propagate changes to database
		update_db_layout(request.user, objects_map, CaptureLayout.objects.filter(capture_batch=capture_batch), 'library', 'reich_lab_library_id')
	elif request.method == 'POST':
		print('POST {capture_batch_name}')
		raise ValueError('unexpected')
		
	layout_elements = CaptureLayout.objects.filter(capture_batch=capture_batch).select_related('library').select_related('control_type')
		
	objects_map = layout_objects_map_for_rendering(layout_elements, 'library', 'reich_lab_library_id')
		
	return render(request, 'samples/generic_layout.html', { 'layout_title': 'Library Layout For Capture', 'layout_name': capture_batch_name, 'rows':PLATE_ROWS, 'columns':WELL_PLATE_COLUMNS, 'objects_map': objects_map,
	'allow_layout_modifications': True })
		#(capture_batch.status == capture_batch.OPEN) } )
		
@login_required
def capture_batch_spreadsheet(request):
	capture_batch_name = request.GET['capture_batch_name']
	capture_batch = CaptureOrShotgunPlate.objects.get(name=capture_batch_name)
	
	response = HttpResponse(content_type='text/csv')
	response['Content-Disposition'] = f'attachment; filename="CaptureOrShotgunPlate_{capture_batch_name}.txt"'

	writer = csv.writer(response, delimiter='\t')
	# header
	writer.writerow(CaptureLayout.spreadsheet_header())
	indexed_libraries = CaptureLayout.objects.filter(capture_batch=capture_batch).order_by('column', 'row', 'library__sample__reich_lab_id')
	for indexed_library in indexed_libraries:
		writer.writerow(indexed_library.to_spreadsheet_row())
	return response

@login_required
def capture_batch_delete(request):
	capture_batch_name = request.GET['batch_name']
	try:
		capture_batch = CaptureOrShotgunPlate.objects.get(name=capture_batch_name)
		capture_batch_form = CaptureBatchForm(instance=capture_batch, user=request.user)
		capture_batch_form.disable_fields()
	except CaptureOrShotgunPlate.DoesNotExist:
		return HttpResponse(f'{capture_batch_name} no longer exists.')
	
	if request.method == 'POST':
		print(f'request to delete {capture_batch_name}')
		capture_batch.delete()
		return redirect(f'{reverse("capture_batches")}')
		
	return render(request, 'samples/delete_batch.html', {'form': capture_batch_form, 'batch_type': 'Capture or Shotgun Batch', 'batch_name': capture_batch_name, 'link': 'capture_batches'})
	
@login_required
def capture_batch_to_sequencing_run(request):
	capture_batch_name = request.GET['capture_batch_name']
	capture_batch = CaptureOrShotgunPlate.objects.get(name=capture_batch_name)
	if request.method == 'POST':
		form = CaptureBatchToSequencingRunForm(request.POST)
		if form.is_valid():
			sequencing_run_name = form.cleaned_data['sequencing_run_name']
			capture_batch.create_sequencing_run(sequencing_run_name, request.user)
			return redirect(f'{reverse("sequencing_runs")}?sequencing_run_name={sequencing_run_name}')
	elif request.method == 'GET':
		form = CaptureBatchToSequencingRunForm()
		# For now, manual only
		form.initial['sequencing_run_name'] = f'{capture_batch_name.rsplit("_")[0]}'
		
	return render(request, 'samples/batch_transition.html', { 'form': form, 
						'source_batch_name': capture_batch_name,
						'source_batch_type': 'Capture or Shotgun Batch',
						'new_batch_type': 'Sequencing Run'
						} )
	
@login_required
def sequencing_runs(request):
	if request.method == 'POST':
		form = SequencingRunForm(request.POST, user=request.user)
		if form.is_valid():
			form.save()
	elif request.method == 'GET':
		form = SequencingRunForm(user=request.user)
		
	sequencing_run_queryset = SequencingRun.objects.all().order_by('-id')
	return render(request, 'samples/sequencing_runs.html', { 'form': form, 'sequencing_runs': sequencing_run_queryset } )
	
@login_required
def sequencing_run_assign_captures(request):
	sequencing_run_name = request.GET['sequencing_run_name']
	sequencing_run = SequencingRun.objects.get(name=sequencing_run_name)
	if request.method == 'POST':
		form = SequencingRunForm(request.POST, user=request.user, instance=sequencing_run)
		
		if form.is_valid():
			form.save()
			
			# disable checkboxes are not in this list, so everything gets removed unless we disable changes
			if sequencing_run.date_pooled is None:
				# these are the ticked checkboxes.
				capture_or_shotgun_plate_ids = request.POST.getlist('sample_checkboxes[]')
				sequencing_run.assign_captures(capture_or_shotgun_plate_ids)
		
	elif request.method == 'GET':
		form = SequencingRunForm(user=request.user, instance=sequencing_run)
	
	# captures already assigned
	assigned_captures = sequencing_run.captures.all()
	# show captures marked as needing sequencing that have not already been assigned
	captures = CaptureOrShotgunPlate.objects.filter(needs_sequencing=True).annotate(sequencing_count=Count('sequencingrun')).exclude(sequencing_count__gt=0)
	
	return render(request, 'samples/sequencing_run_assign_captures.html', { 'sequencing_run_name': sequencing_run_name, 'sequencing_run': sequencing_run,  'form': form, 'assigned_captures': assigned_captures, 'unassigned_captures': captures} )
	
@login_required
def sequencing_run_spreadsheet(request):
	sequencing_run_name = request.GET['sequencing_run_name']
	sequencing_run = SequencingRun.objects.get(name=sequencing_run_name)
	
	response = HttpResponse(content_type='text/csv')
	response['Content-Disposition'] = f'attachment; filename="{sequencing_run_name}_ESS.txt"'

	writer = csv.writer(response, delimiter='\t')
	# header
	writer.writerow(CaptureLayout.spreadsheet_header())
	for indexed_library in sequencing_run.indexed_libraries.all().order_by('column', 'row'):
		writer.writerow(indexed_library.to_spreadsheet_row())
	return response

@login_required
def sequencing_run_delete(request):
	sequencing_run_name = request.GET['batch_name']
	try:
		sequencing_run = SequencingRun.objects.get(name=sequencing_run_name)
		sequencing_run_form = SequencingRunForm(instance=sequencing_run, user=request.user)
		sequencing_run_form.disable_fields()
	except CaptureOrShotgunPlate.DoesNotExist:
		return HttpResponse(f'{sequencing_run_name} no longer exists.')
	
	if request.method == 'POST':
		print(f'request to delete {sequencing_run_name}')
		sequencing_run.delete()
		return redirect(f'{reverse("sequencing_runs")}')
		
	return render(request, 'samples/delete_batch.html', {'form': sequencing_run_form, 'batch_type': 'Sequencing Run', 'batch_name': sequencing_run_name, 'link': 'sequencing_runs'})
	
@login_required
def sequencing_platforms(request):
	if request.method == 'POST':
		form = SequencingPlatformForm(request.POST, user=request.user)
		if form.is_valid():
			form.save()
	elif request.method == 'GET':
		form = SequencingPlatformForm(user=request.user)
		
	sequencing_platform_queryset = SequencingPlatform.objects.all().order_by('-id')
	return render(request, 'samples/sequencing_platforms.html', { 'form': form, 'sequencing_platforms': sequencing_platform_queryset } )
	
@login_required
def sequencing_platform(request):
	sequencing_platform_id = request.GET['sequencing_platform_id']
	sequencing_platform = SequencingPlatform.objects.get(id=sequencing_platform_id)
	if request.method == 'POST':
		form = SequencingPlatformForm(request.POST, user=request.user)
		if form.is_valid():
			form.save()
	elif request.method == 'GET':
		form = SequencingPlatformForm(user=request.user, instance=sequencing_platform)
		
	return render(request, 'samples/generic_form.html', { 'title': f'Sequencing Platform {str(sequencing_platform)}', 'form': form, } )

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
	
@login_required
def setup(request):
	return render(request, 'samples/setup.html', {})
		
def logout_user(request):
	return logout_then_login(request)

@login_required
def password_changed(request):
	return render(request, 'samples/password_changed.html', {} )
