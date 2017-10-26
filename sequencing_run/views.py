from django.shortcuts import render

from django.http import HttpResponse
from django.http import HttpResponseRedirect

from sequencing_run.ssh_command import ssh_command
from sequencing_run.models import SequencingRun
from sequencing_run.screening_analysis import start_screening_analysis

from .forms import ScreeningAnalysisForm

# Create your views here.
def index(request):
	HOST="mym11@transfer.rc.hms.harvard.edu"
	COMMAND="uname -a | tee ~/testout"

	ssh = ssh_command(HOST, COMMAND)
	result = ssh.stdout.readlines()
	return HttpResponse(result)
	#return HttpResponse("Hello, world.")

# Look at the Genetics file server to retrieve sequencing runs list
def updateSequencingRunList(request):
	host = "mym11@transfer.rc.hms.harvard.edu"
	command = "ls /files/Genetics/reichseq/reich/reichseq/reich"

	ssh_result = ssh_command(host, command)
	result = ssh_result.stdout.readlines()
	# this is a list of directories with sequencing data
	# write these to the database so the user can select which directory to use
	for directory in result:
		s, created = SequencingRun.objects.get_or_create(illumina_directory = directory.decode('utf-8').strip() )
	
	return HttpResponse(result)

def screeningForm(request):
	# if this is a POST request we need to process the form data
	if request.method == 'POST':
		# create a form instance and populate it with data from the request:
		form = ScreeningAnalysisForm(request.POST)
		# check whether it's valid:
		if form.is_valid():
			print('Valid form')
			# process the data in form.cleaned_data as required
			# ...
			#print(form.cleaned_data['illumina_directory'])
			start_screening_analysis(
				form.cleaned_data['illumina_directory'],
				form.cleaned_data['name'],
				form.cleaned_data['sequencing_date'],
				form.cleaned_data['top_samples_to_demultiplex'])
			# redirect to a new URL:
			return HttpResponseRedirect('/sequencing_run/start/')

    # if a GET (or any other method) we'll create a blank form
	else:
		updateSequencingRunList(request) # argument is not used
		form = ScreeningAnalysisForm()

	return render(request, 'sequencing_run/screening.html', {'form': form})

def startScreeningAnalysis(request):
	print('Request to start')
	return HttpResponse('Request to start')
