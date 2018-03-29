from django import forms

from .models import SequencingRun, SequencingRunID
from .models import Flowcell

class StatusForm(forms.Form):
	illumina_directory = forms.ModelChoiceField(queryset=SequencingRun.objects.all().order_by('-illumina_directory'), label='Illumina directory', empty_label='Illumina directory', to_field_name='illumina_directory')

class AnalysisForm(forms.Form):
	illumina_directory = forms.ModelChoiceField(queryset=SequencingRun.objects.all().order_by('-illumina_directory'), label='Illumina directory', empty_label='Illumina directory', to_field_name='illumina_directory')
	name = forms.ModelChoiceField(queryset=SequencingRunID.objects.all().order_by('-order'), label="sequencing run name", )
	sequencing_date = forms.DateField(label='Sequencing Date (YYYY-MM-DD)')
	top_samples_to_demultiplex = forms.IntegerField(label='# most common samples to demultiplex', initial=150, min_value=1, max_value=1000)
	

	flowcell1 = forms.ModelChoiceField(queryset=Flowcell.objects.all().order_by('-sequencing_date'), label='Past flowcell to analyze with', empty_label='', to_field_name='flowcell_text_id', required=False)
	flowcell2 = forms.ModelChoiceField(queryset=Flowcell.objects.all().order_by('-sequencing_date'), label='Past flowcell to analyze with', empty_label='', to_field_name='flowcell_text_id', required=False)
	flowcell3 = forms.ModelChoiceField(queryset=Flowcell.objects.all().order_by('-sequencing_date'), label='Past flowcell to analyze with', empty_label='', to_field_name='flowcell_text_id', required=False)
	flowcell4 = forms.ModelChoiceField(queryset=Flowcell.objects.all().order_by('-sequencing_date'), label='Past flowcell to analyze with', empty_label='', to_field_name='flowcell_text_id', required=False)

	#flowcells = forms.ModelMultipleChoiceField(queryset=Flowcell.objects.all().order_by('-sequencing_date'), required=False)

class ReportWithSampleSheetForm(forms.Form):
	report_file = forms.FileField(help_text='Analysis or demultiplexing statistics report')
	sample_sheet_file = forms.FileField(help_text='Sample sheet file in tab-delimited text format')
