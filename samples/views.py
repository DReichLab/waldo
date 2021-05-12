from django.core.paginator import Paginator
from django.shortcuts import render

from django.http import HttpResponse

from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import logout_then_login

import csv
import json
from datetime import datetime

from samples.pipeline import udg_and_strandedness
from samples.models import Results, Library, Sample, PowderBatch, WetLabStaff
from .forms import IndividualForm, LibraryIDForm, PowderBatchForm
from sequencing_run.models import MTAnalysis

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
def powder_batch(request):
	return sample_selection(request)

@login_required
def sample_selection(request):
	if request.method == 'POST':
		powder_batch_name = request.POST['name']
		form = PowderBatchForm(request.POST)
		if form.is_valid():
			powder_batch = PowderBatch.objects.get(name=powder_batch_name)
			
			name = form.cleaned_data['name']
			date = form.cleaned_data['date']
			status = form.cleaned_data['status']
			notes = form.cleaned_data['notes']
			
			powder_batch.name = name
			powder_batch.date = date
			powder_batch.status = status
			powder_batch.notes = notes
			powder_batch.save()
		else:
			return HttpResponse("Invalid form")
		
	elif request.method == 'GET':
		powder_batch_name = request.GET['name']
		powder_batch = PowderBatch.objects.get(name=powder_batch_name)
		form = PowderBatchForm(initial={'name': powder_batch_name, 'date': powder_batch.date, 'status': powder_batch.status, 'notes': powder_batch.notes})
	
	# open can have new samples assigned
	sample_queue = Sample.objects.filter(queue_id__isnull=False, reich_lab_id__isnull=True).order_by('queue_id')
	return render(request, 'samples/sample_selection.html', { 'samples': sample_queue, 'powder_batch_name': powder_batch_name, 'form': form } )
	
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
