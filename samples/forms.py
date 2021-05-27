from django import forms
from django.forms import ModelChoiceField, ChoiceField, FileField, ModelForm, Textarea
from django.forms import modelformset_factory

from samples.models import PowderBatchStatus, PowderSample, Sample, SamplePrepProtocol

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

class PowderBatchForm(forms.Form):
	name = forms.CharField(max_length=50)
	date = forms.DateField(initial=datetime.date.today)
	status = PowderBatchStatusSelect(queryset=PowderBatchStatus.objects.all().order_by('sort_order'), empty_label=None)
	notes = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 2})) 

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
	sample_prep_protocol = SamplePrepProtocolSelect(queryset=SamplePrepProtocol.objects.all(), empty_label=None)
	class Meta:
		model = PowderSample
		fields = ['sampling_tech', 'sampling_notes', 'total_powder_produced_mg', 'storage_location', 'sample_prep_lab', 'sample_prep_protocol']
		widgets = {
            'sampling_notes': Textarea(attrs={'cols': 60, 'rows': 2}),
        }
		
PowderSampleFormset = modelformset_factory(PowderSample, form=PowderSampleForm, extra=0, max_num=200)
		
class PowderSampleFormsetHelper(FormHelper):
	def __init__(self, *args, **kwargs):
		super(PowderSampleFormsetHelper, self).__init__(*args, **kwargs)
		self.layout = Layout('sampling_tech', 'sampling_notes', 'total_powder_produced_mg', 'storage_location', 'sample_prep_lab', 'sample_prep_protocol')
		self.template = 'bootstrap/table_inline_formset.html'
