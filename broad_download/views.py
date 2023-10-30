from django.shortcuts import render
from django.conf import settings
from django.http import HttpResponse

from sequencing_run.ssh_command import ssh_command

from .models import FlowcellDownload
from .forms import DownloadForm

# Create your views here.
def flowcell_download(request):
	# if this is a POST request we need to process the form data
	if request.method == 'POST':
		# create a form instance and populate it with data from the request:
		form = DownloadForm(request.POST)
		# check whether it's valid:
		if form.is_valid():
			name = form.cleaned_data['name']
			password = form.cleaned_data['password']
			try:
				download = FlowcellDownload.objects.get(name=name)
				download.password = password
			except FlowcellDownload.DoesNotExist as error:
				download = FlowcellDownload(name=name, password=password)
			download.save()
			
			# start download on transfer server
			host = settings.TRANSFER_HOST
			command = 'cd /n/standby/hms/genetics/reich/compute/sequencing/broad; bash broad_download.sh {} {}'.format(name, password)
			#print('running: {}'.format(command))
			ssh_command(host, command)
				
	 # if a GET (or any other method) we'll create a blank form
	else:
		form = DownloadForm()
	
	downloads = FlowcellDownload.objects.all().order_by('pk').reverse()[:30]
		
	return render(request, 'broad_download/download.html', {'form': form, 'downloads': downloads })
