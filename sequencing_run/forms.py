from django import forms

from sequencing_run.models import SequencingRun
from sequencing_run.models import Flowcell

class StatusForm(forms.Form):
	illumina_directory = forms.ModelChoiceField(queryset=SequencingRun.objects.all().order_by('-illumina_directory'), label='Illumina directory', empty_label='Illumina directory', to_field_name='illumina_directory')

class AnalysisForm(forms.Form):
	illumina_directory = forms.ModelChoiceField(queryset=SequencingRun.objects.all().order_by('-illumina_directory'), label='Illumina directory', empty_label='Illumina directory', to_field_name='illumina_directory')
	name = forms.RegexField(label="sequencing run name", regex='^[0-9a-zA-Z\-\_]+$', min_length=1,  max_length=100, help_text="Alphanumeric with '-' and '_' allowed")
	sequencing_date = forms.DateField(label='Sequencing Date (YYYY-MM-DD)')
	top_samples_to_demultiplex = forms.IntegerField(label='# most common samples to demultiplex', initial=150, min_value=1, max_value=1000)
	

	flowcell1 = forms.ModelChoiceField(queryset=Flowcell.objects.all().order_by('-sequencing_date'), label='Past flowcell to analyze with', empty_label='', to_field_name='flowcell_text_id', required=False)
	flowcell2 = forms.ModelChoiceField(queryset=Flowcell.objects.all().order_by('-sequencing_date'), label='Past flowcell to analyze with', empty_label='', to_field_name='flowcell_text_id', required=False)
	flowcell3 = forms.ModelChoiceField(queryset=Flowcell.objects.all().order_by('-sequencing_date'), label='Past flowcell to analyze with', empty_label='', to_field_name='flowcell_text_id', required=False)
	flowcell4 = forms.ModelChoiceField(queryset=Flowcell.objects.all().order_by('-sequencing_date'), label='Past flowcell to analyze with', empty_label='', to_field_name='flowcell_text_id', required=False)

	#flowcells = forms.ModelMultipleChoiceField(queryset=Flowcell.objects.all().order_by('-sequencing_date'), required=False)
