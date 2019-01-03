from django.shortcuts import render

from django.http import HttpResponse
from django.http import HttpResponseRedirect

from django.conf import settings

from sequencing_run.ssh_command import ssh_command
from .models import SequencingRun, SequencingRunID, SequencingAnalysisRun, Flowcell
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
	host = settings.TRANSFER_HOST
	command = "ls -t {}".format(settings.FILES_SERVER_DIRECTORY)

	ssh_result = ssh_command(host, command)
	result = ssh_result.stdout.readlines()
	# this is a list of directories with sequencing data
	# write these to the database so the user can select which directory to use
	# for performance, only update the most recent 10 entries
	for directory in result[0:10]:
		s, created = SequencingRun.objects.get_or_create(illumina_directory = directory.strip() )
	
	return HttpResponse(result)

# populate dropdown for sequencing run name
def update_sequencing_run_ids():
	host = settings.COMMAND_HOST
	query = "SELECT sequenced_library_key, sequencing_id FROM sequenced_library GROUP BY sequencing_id ORDER BY sequenced_library_key DESC;"
	command = "mysql devadna -N -e '{}'".format(query)
	ssh_result = ssh_command(host, command)
	result = ssh_result.stdout.readlines()
	for line in result:
		try:
			numerical_id, name = line.strip().split('\t')
			if name != None and len(name) > 0:
				s, created = SequencingRunID.objects.get_or_create(name=name.strip(), order=int(numerical_id))
		except:
			pass

def analysis_form(request):
	# always retreive the list of active screening runs
	run_list = SequencingAnalysisRun.objects.all().order_by('pk').reverse()[:40]
	
	slurm_jobs = []
	
	# if this is a POST request we need to process the form data
	if request.method == 'POST':
		# create a form instance and populate it with data from the request:
		form = AnalysisForm(request.POST)
		# check whether it's valid:
		if form.is_valid():
			print('Valid form')
			
			# construct a single name from all names attached to this sequencing run
			sequencing_run_names = []
			for widget_name in ['name1', 'name2', 'name3', 'name4']:
				name_object = form.cleaned_data[widget_name]
				if name_object != None:
					sequencing_run_names.append(name_object.name)
			
			sequencing_run_name = '_'.join(sequencing_run_names)
			print(sequencing_run_names)
			print(sequencing_run_name)
			
			if 'start_analysis' in request.POST:
				# process the data in form.cleaned_data as required
				# ...
				#print(form.cleaned_data['illumina_directory'])
				orchestra_thread = threading.Thread(
					target=start_analysis,
					args=(
						str(form.cleaned_data['illumina_directory']),
						sequencing_run_name,
						form.cleaned_data['sequencing_date'],
						form.cleaned_data['top_samples_to_demultiplex'],
						sequencing_run_names,
					)
				)
				orchestra_thread.start()
				# redirect to a new URL:
				return HttpResponseRedirect('/sequencing_run/start/')
			elif 'get_report' in request.POST:
				date_string = form.cleaned_data['sequencing_date'].strftime("%Y%m%d")
				filename = date_string + '_' + sequencing_run_name + '.report.txt'
				report = get_final_report(date_string, sequencing_run_name)
				response = HttpResponse(report, content_type='text/txt')
				response['Content-Disposition'] = 'attachment; filename="' + filename + '"'
				return response
			elif 'get_kmer' in request.POST:
				date_string = form.cleaned_data['sequencing_date'].strftime("%Y%m%d")
				filename = date_string + '_' + sequencing_run_name + '.kmer.txt'
				report = get_kmer_analysis(date_string, sequencing_run_name)
				response = HttpResponse(report, content_type='text/txt')
				response['Content-Disposition'] = 'attachment; filename="' + filename + '"'
				return response
			elif 'get_demultiplex_report' in request.POST:
				date_string = form.cleaned_data['sequencing_date'].strftime("%Y%m%d")
				filename = date_string + '_' + sequencing_run_name + '.demultiplex_report.txt'
				report = get_demultiplex_report(date_string, sequencing_run_name)
				response = HttpResponse(report, content_type='text/txt')
				response['Content-Disposition'] = 'attachment; filename="' + filename + '"'
				return response

    # if a GET (or any other method) we'll create a blank form
	else:
		update_sequencing_run_list(request) # argument is not used
		update_sequencing_run_ids()
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
			
			sample_sheet_lines = sample_sheet_file.read().decode('utf-8', 'ignore').splitlines()
			
			sample_parameters = readSampleSheet_array(sample_sheet_lines)
			
			sampleLines = relabelSampleLines_array([line.decode('utf-8') for line in report_file.readlines()], sample_parameters)
			report = '\n'.join(sampleLines)
			response = HttpResponse(report, content_type='text/txt')
			response['Content-Disposition'] = 'attachment; filename="{}"'.format(report_file.name)
			return response
	# if a GET (or any other method) we'll create a blank form
	else:
		form = ReportWithSampleSheetForm()
	
	return render(request, 'sequencing_run/report_with_sample_sheet.html', {'form': form})
