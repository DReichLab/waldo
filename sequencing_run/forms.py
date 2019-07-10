from django import forms
from django.db.models.functions import Length

from .models import SequencingRun, SequencingRunID
from .models import Flowcell

# only display sequencing run (illumina directory strings) with length > 25
# These are the NextSeq runs on the Genetics file server, as opposed to the fake Broad entries, which are not 

class StatusForm(forms.Form):
	illumina_directory = forms.ModelChoiceField(queryset=SequencingRun.objects.annotate(text_len=Length('illumina_directory')).filter(text_len__gt=25).order_by('-illumina_directory'), label='Illumina directory', empty_label='Illumina directory', to_field_name='illumina_directory')

class AnalysisForm(forms.Form):
	illumina_directory = forms.ModelChoiceField(queryset=SequencingRun.objects.annotate(text_len=Length('illumina_directory')).filter(text_len__gt=25).order_by('-illumina_directory'), label='Illumina directory', empty_label='Illumina directory', to_field_name='illumina_directory')
	name1 = forms.ModelChoiceField(queryset=SequencingRunID.objects.all().order_by('-order'), label="sequencing run name", )
	name2 = forms.ModelChoiceField(queryset=SequencingRunID.objects.all().order_by('-order'), label="sequencing run name (optional)", required=False)
	name3 = forms.ModelChoiceField(queryset=SequencingRunID.objects.all().order_by('-order'), label="sequencing run name (optional)", required=False)
	name4 = forms.ModelChoiceField(queryset=SequencingRunID.objects.all().order_by('-order'), label="sequencing run name (optional)", required=False)
	sequencing_date = forms.DateField(label='Sequencing Date (YYYY-MM-DD)')
	top_samples_to_demultiplex = forms.IntegerField(label='# most common samples to demultiplex', initial=200, min_value=1, max_value=1000)

class ReportWithSampleSheetForm(forms.Form):
	report_file = forms.FileField(help_text='Analysis or demultiplexing statistics report')
	sample_sheet_file = forms.FileField(help_text='Sample sheet file in tab-delimited text format')
