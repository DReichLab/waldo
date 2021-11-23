from django import forms
from django.forms import ModelForm

from .models import FlowcellDownload

class DownloadForm(ModelForm):
	class Meta:
		model = FlowcellDownload
		fields = 'name', 'password'
