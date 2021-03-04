from django.shortcuts import render

from django.http import HttpResponse

import csv
import json

from samples.pipeline import udg_and_strandedness
from samples.models import Results, Library
from .forms import IndividualForm, LibraryIDForm
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
	
# Handle the layout of a 96 well plate with libraries
# This renders an interface allowing a technician to move libraries between wells
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
		
