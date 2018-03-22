from django.shortcuts import render

from django.http import HttpResponse
from django.http import HttpResponseRedirect

from django.conf import settings

from sequencing_run.ssh_command import ssh_command
from sequencing_run.models import SequencingRun, SequencingAnalysisRun
from sequencing_run.analysis import start_analysis, query_job_status, get_kmer_analysis, get_final_report, get_demultiplex_report
from sequencing_run.report_field_descriptions import report_field_descriptions
from .report_match_samples import readSampleSheet_array, relabelSampleLines_array

from .forms import AnalysisForm, ReportWithSampleSheetForm

import threading

# Create your views here.
def index(request):
	HOST=settings.TRANSFER_HOST
	COMMAND="uname -a | tee ~/testout"

	ssh = ssh_command(HOST, COMMAND)
	result = ssh.stdout.readlines()
	return HttpResponse(result)
	#return HttpResponse("Hello, world.")
	
def help_page(request):
	return render(request, 'sequencing_run/help.html', {'report_fields': report_field_descriptions(request)})

# Look at the Genetics file server to retrieve sequencing runs list
def update_sequencing_run_list(request):
	host = HOST=settings.TRANSFER_HOST
	command = "ls {}".format(settings.FILES_SERVER_DIRECTORY)

	ssh_result = ssh_command(host, command)
	result = ssh_result.stdout.readlines()
	# this is a list of directories with sequencing data
	# write these to the database so the user can select which directory to use
	for directory in result:
		s, created = SequencingRun.objects.get_or_create(illumina_directory = directory.strip() )
	
	return HttpResponse(result)

def add_to_set_non_none(the_set, item):
	if item != None:
		the_set.add(item)
	return the_set

def analysis_form(request):
	# always retreive the list of active screening runs
	run_list = SequencingAnalysisRun.objects.all().order_by('pk').reverse()[:20]
	
	slurm_jobs = []
	
	# if this is a POST request we need to process the form data
	if request.method == 'POST':
		# create a form instance and populate it with data from the request:
		form = AnalysisForm(request.POST)
		# check whether it's valid:
		if form.is_valid():
			print('Valid form')
			if 'start_analysis' in request.POST:
				# process the data in form.cleaned_data as required
				# ...
				#print(form.cleaned_data['illumina_directory'])
				flowcell_set = set()
				add_to_set_non_none(flowcell_set, form.cleaned_data['flowcell1'])
				add_to_set_non_none(flowcell_set, form.cleaned_data['flowcell2'])
				add_to_set_non_none(flowcell_set, form.cleaned_data['flowcell3'])
				add_to_set_non_none(flowcell_set, form.cleaned_data['flowcell4'])
				flowcells = list(flowcell_set)
				print(flowcells)
				orchestra_thread = threading.Thread(
					target=start_analysis,
					args=(
						str(form.cleaned_data['illumina_directory']),
						form.cleaned_data['name'],
						form.cleaned_data['sequencing_date'],
						form.cleaned_data['top_samples_to_demultiplex'],
						flowcells,
					)
				)
				orchestra_thread.start()
				# redirect to a new URL:
				return HttpResponseRedirect('/sequencing_run/start/')
			elif 'get_report' in request.POST:
				date_string = form.cleaned_data['sequencing_date'].strftime("%Y%m%d")
				filename = date_string + '_' + form.cleaned_data['name'] + '.report.txt'
				report = get_final_report(date_string, form.cleaned_data['name'])
				response = HttpResponse(report, content_type='text/txt')
				response['Content-Disposition'] = 'attachment; filename="' + filename + '"'
				return response
			elif 'get_kmer' in request.POST:
				date_string = form.cleaned_data['sequencing_date'].strftime("%Y%m%d")
				filename = date_string + '_' + form.cleaned_data['name'] + '.kmer.txt'
				report = get_kmer_analysis(date_string, form.cleaned_data['name'])
				response = HttpResponse(report, content_type='text/txt')
				response['Content-Disposition'] = 'attachment; filename="' + filename + '"'
				return response
			elif 'get_demultiplex_report' in request.POST:
				date_string = form.cleaned_data['sequencing_date'].strftime("%Y%m%d")
				filename = date_string + '_' + form.cleaned_data['name'] + '.demultiplex_report.txt'
				report = get_demultiplex_report(date_string, form.cleaned_data['name'])
				response = HttpResponse(report, content_type='text/txt')
				response['Content-Disposition'] = 'attachment; filename="' + filename + '"'
				return response

    # if a GET (or any other method) we'll create a blank form
	else:
		update_sequencing_run_list(request) # argument is not used
		slurm_jobs = query_job_status()
		form = AnalysisForm()

	return render(request, 'sequencing_run/analysis.html', {'form': form, 'analysis_run_list': run_list, 'slurm_jobs': slurm_jobs, 'processing_state_demultiplex_threshold': SequencingAnalysisRun.RUNNING_ANALYSIS, 'processing_state_report_threshold': SequencingAnalysisRun.RUNNING_ANALYSIS_PRELIMINARY_REPORT_DONE})

def start_analysis_view(request):
	print('Request to start')
	return HttpResponse('Requested to start processing. Return to <a href="/sequencing_run/">status page</a>')

def report_with_sample_sheet_form(request):
	# if this is a POST request we need to process the form data
	if request.method == 'POST':
		# create a form instance and populate it with data from the request:
		form = ReportWithSampleSheetForm(request.POST, request.FILES)
		# check whether it's valid:
		if form.is_valid():
			print('Valid report with sample sheet form')
			#if 'start_analysis' in request.POST:
			report_file = request.FILES['report_file']
			sample_sheet_file = request.FILES['sample_sheet_file']
			
			print(report_file.name)
			print(sample_sheet_file.name)
			libraryIDs, plateIDs = readSampleSheet_array([line.decode('utf-8') for line in sample_sheet_file.readlines()])
			sampleLines = relabelSampleLines_array([line.decode('utf-8') for line in report_file.readlines()], libraryIDs, plateIDs)
			report = '\n'.join(sampleLines)
			response = HttpResponse(report, content_type='text/txt')
			response['Content-Disposition'] = 'attachment; filename="{}"'.format(report_file.name)
			return response
	# if a GET (or any other method) we'll create a blank form
	else:
		form = ReportWithSampleSheetForm()
	
	return render(request, 'sequencing_run/report_with_sample_sheet.html', {'form': form})
