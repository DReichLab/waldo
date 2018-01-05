from django import forms

from sequencing_run.models import SequencingRun

class StatusForm(forms.Form):
	illumina_directory = forms.ModelChoiceField(queryset=SequencingRun.objects.all().order_by('-illumina_directory'), label='Illumina directory', empty_label='Illumina directory', to_field_name='illumina_directory')

class ScreeningAnalysisForm(forms.Form):
	illumina_directory = forms.ModelChoiceField(queryset=SequencingRun.objects.all().order_by('-illumina_directory'), label='Illumina directory', empty_label='Illumina directory', to_field_name='illumina_directory')
	name = forms.RegexField(label="sequencing run name", regex='^[0-9a-zA-Z\-\_]+$', min_length=1,  max_length=100, help_text="Alphanumeric with '-' and '_' allowed")
	sequencing_date = forms.DateField(label='Sequencing Date (YYYY-MM-DD)')
	top_samples_to_demultiplex = forms.IntegerField(label='# most common samples to demultiplex', initial=500, min_value=50, max_value=1000)
