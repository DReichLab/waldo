from django import forms
from django.forms import ModelChoiceField, ChoiceField, FileField, ModelForm, Textarea, CharField
from django.forms import modelformset_factory

from samples.models import PowderBatch, PowderBatchStatus, PowderSample, Sample, SamplePrepProtocol, ControlType, ControlLayout, ExtractBatch, ExtractionProtocol

from crispy_forms.helper import FormHelper, Layout

import datetime

class IndividualForm(forms.Form):
	individual_id = forms.IntegerField(label='Reich Lab Individual ID') 

class LibraryIDForm(forms.Form):
	library_id = forms.CharField(max_length=20, min_length=7, label='Reich Lab Library ID')

# to display the powder batch status description instead of a primary key
class PowderBatchStatusSelect(ModelChoiceField):
	def label_from_instance(self, obj):
		return obj.description

class PowderBatchForm(ModelForm):
	date = forms.DateField(initial=datetime.date.today)
	status = PowderBatchStatusSelect(queryset=PowderBatchStatus.objects.all().order_by('sort_order'), empty_label=None)
	notes = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 2})) 
	class Meta:
		model = PowderBatch
		fields = ['name', 'date', 'status', 'notes']

IMAGE_TYPES = [
		('Before', 'Before'),
		('After', 'After'),
		('C14', 'C14')
	]

class SampleImageForm(forms.Form):
	image_type = forms.ChoiceField(choices=IMAGE_TYPES)
	photo = forms.FileField()

# to display sample with Reich Lab sample number, S6113
class SampleSelect(ModelChoiceField):
	def label_from_instance(self, obj):
		return f'S{obj.reich_lab_id}'
	
# to display the sample prep protocol method instead of a primary key
class SamplePrepProtocolSelect(ModelChoiceField):
	def label_from_instance(self, obj):
		return obj.preparation_method
	
class PowderSampleForm(ModelForm):
	reich_lab_sample = CharField(disabled=True)
	sample_prep_protocol = SamplePrepProtocolSelect(queryset=SamplePrepProtocol.objects.all(), empty_label=None)
	class Meta:
		model = PowderSample
		#'powder_sample_id', 
		fields = ['reich_lab_sample', 'sampling_notes', 'total_powder_produced_mg', 'storage_location', 'sample_prep_lab', 'sample_prep_protocol']
		widgets = {
            'sampling_notes': Textarea(attrs={'cols': 60, 'rows': 2}),
        }
		
	def __init__(self, *args, **kwargs):
		super(PowderSampleForm, self).__init__(*args, **kwargs)
		if self.instance.pk:
			self.fields['reich_lab_sample'].initial = f'S{self.instance.sample.reich_lab_id}'
			#self.fields['powder_sample_id'].disabled = True
		
PowderSampleFormset = modelformset_factory(PowderSample, form=PowderSampleForm, extra=0, max_num=200)
		
class PowderSampleFormsetHelper(FormHelper):
	def __init__(self, *args, **kwargs):
		super(PowderSampleFormsetHelper, self).__init__(*args, **kwargs)
		self.layout = Layout('sampling_tech', 'sampling_notes', 'total_powder_produced_mg', 'storage_location', 'sample_prep_lab', 'sample_prep_protocol')
		self.template = 'bootstrap/table_inline_formset.html'
		
class ExtractionProtocolForm(ModelForm):
	class Meta:
		model = ExtractionProtocol
		fields = ['name', 'start_date', 'end_date', 'description', 'manual_robotic', 'total_lysis_volume', 'lysate_fraction_extracted', 'final_extract_volume', 'binding_buffer', 'manuscript_summary', 'protocol_reference']

ExtractionProtocolFormset = modelformset_factory(ExtractionProtocol, form=ExtractionProtocolForm, extra=0, max_num=100)
		
# to display the sample prep protocol method instead of a primary key
class ExtractionProtocolSelect(ModelChoiceField):
	def label_from_instance(self, obj):
		return obj.name
		
class ExtractBatchForm(ModelForm):
	protocol = ExtractionProtocolSelect(queryset=ExtractionProtocol.objects.all())
	class Meta:
		model = ExtractBatch
		fields = ['batch_name', 'protocol', 'date', 'robot', 'note']
		widgets = {
			'note': Textarea(attrs={'cols': 60, 'rows': 2}),
		}
		
class ControlTypeSelect(ModelChoiceField):
	def label_from_instance(self, obj):
		return obj.control_type
		
class ControlTypeForm(ModelForm):
	class Meta:
		fields = ['control_type']
		
ControlTypeFormset = modelformset_factory(ControlType, form=ControlTypeForm, max_num=20)

class ControlLayoutForm(ModelForm):
	control_type = ControlTypeSelect(queryset=ControlType.objects.all(), empty_label=None)
	class Meta:
		model = ControlLayout
		fields = ['layout_name', 'row', 'column', 'control_type', 'active']

ControlLayoutFormset = modelformset_factory(ControlLayout, form=ControlLayoutForm)
