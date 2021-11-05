from django import forms
from django.forms import ModelChoiceField, ChoiceField, FileField, ModelForm, Textarea, IntegerField, CharField, BoundField, ValidationError
from django.forms import modelformset_factory
from django.forms.widgets import TextInput
from django.utils.translation import gettext_lazy as _

from samples.models import PowderBatch, PowderBatchStatus, PowderSample, Sample, SamplePrepProtocol, ControlType, ControlSet, ControlLayout, LysateBatch, ExtractionProtocol, ExpectedComplexity, SamplePrepQueue, Lysate, LysateBatchLayout, ExtractionBatch, ExtractionBatchLayout, LibraryProtocol, LibraryBatch, Extract, Storage, Library, Barcode, NuclearCaptureProtocol, NuclearCapturePlate

import datetime

class IndividualForm(forms.Form):
	individual_id = forms.IntegerField(label='Reich Lab Individual ID') 

class LibraryIDForm(forms.Form):
	library_id = forms.CharField(max_length=20, min_length=7, label='Reich Lab Library ID')

# to display the powder batch status description instead of a primary key
class PowderBatchStatusSelect(ModelChoiceField):
	def label_from_instance(self, obj):
		return obj.description

# This is basically a ModelForm with an additional user (Django login object) field for tracking who has modified objects in the save method
class UserModelForm(ModelForm):
	def __init__(self, *args, user, **kwargs):
		self.user = user
		super().__init__(*args, **kwargs)
		
	def save(self, commit=True):
		m = super().save(commit=False)
		m.save_user = self.user
		if commit:
			m.save()
		return m
	
	class Meta:
		abstract = True

class PowderBatchForm(UserModelForm):
	date = forms.DateField(help_text='YYYY-MM-DD', required=False)
	status = PowderBatchStatusSelect(queryset=PowderBatchStatus.objects.all().order_by('sort_order'), empty_label=None)
	notes = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 2})) 
	class Meta:
		model = PowderBatch
		fields = ['name', 'date', 'technician', 'status', 'notes']
		
	def disable_fields(self):
		for field in PowderBatchForm._meta.fields:
			self.fields[field].disabled = True

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
	
class ExpectedComplexitySelect(ModelChoiceField):
	def label_from_instance(self, obj):
		return obj.description

class SampleByQueueIDField(IntegerField):
	def clean(self, value):
		try:
			return Sample.objects.get(queue_id=value)
		except Sample.DoesNotExist:
			raise ValidationError(_('Sample with queue id {value} does not exist'), code='exist')
	
class SamplePrepQueueForm(UserModelForm):
	sample_queue_id = SampleByQueueIDField(label='Sample Queue ID')
	sample_prep_protocol = SamplePrepProtocolSelect(queryset=SamplePrepProtocol.objects.all(), empty_label=None)
	class Meta:
		model = SamplePrepQueue
		fields = ['sample_queue_id', 'priority', 'sample_prep_protocol', 'udg_treatment']
	def __init__(self, *args, **kwargs):
		super(SamplePrepQueueForm, self).__init__(*args, **kwargs)
		try:
			#print(f'SamplePrepQueueForm {self.instance.sample.queue_id}')
			self.fields['sample_queue_id'].initial = self.instance.sample.queue_id
		except Sample.DoesNotExist:
			self.fields['sample_queue_id'].initial = None
			
	def save(self, commit=True):
		model = super(SamplePrepQueueForm, self).save(commit=False)
		sample = self.cleaned_data['sample_queue_id']
		if sample:
			model.sample = sample
		if commit:
			model.save()
		return model
        
SamplePrepQueueFormset = modelformset_factory(SamplePrepQueue, form=SamplePrepQueueForm, extra=0)
	
class PowderSampleForm(UserModelForm):
	reich_lab_sample = CharField(disabled=True)
	sample_prep_protocol = SamplePrepProtocolSelect(queryset=SamplePrepProtocol.objects.all(), empty_label=None)
	class Meta:
		model = PowderSample
		#'powder_sample_id', 
		fields = ['reich_lab_sample', 'powder_sample_id', 'sampling_notes', 'total_powder_produced_mg', 'powder_for_extract', 'storage_location', 'sample_prep_lab', 'sample_prep_protocol']
		widgets = {
            'sampling_notes': Textarea(attrs={'cols': 60, 'rows': 2}),
        }
		
	def __init__(self, *args, **kwargs):
		super(PowderSampleForm, self).__init__(*args, **kwargs)
		if self.instance.pk:
			self.fields['reich_lab_sample'].initial = f'S{self.instance.sample.reich_lab_id}'
		self.fields['powder_sample_id'].disabled = True
		
PowderSampleFormset = modelformset_factory(PowderSample, form=PowderSampleForm, extra=0, max_num=200)
		
class ExtractionProtocolForm(UserModelForm):
	class Meta:
		model = ExtractionProtocol
		fields = ['name', 'start_date', 'end_date', 'description', 'manual_robotic', 'total_lysis_volume', 'lysate_fraction_extracted', 'final_extract_volume', 'binding_buffer', 'manuscript_summary', 'protocol_reference', 'active']

ExtractionProtocolFormset = modelformset_factory(ExtractionProtocol, form=ExtractionProtocolForm, extra=0, max_num=100)
		
# to display the extraction protocol method instead of a primary key
class ExtractionProtocolSelect(ModelChoiceField):
	def label_from_instance(self, obj):
		return obj.name
		
# to display the powder batch status description instead of a primary key
class ControlSetSelect(ModelChoiceField):
	def label_from_instance(self, obj):
		return obj.layout_name
		
class ControlSetForm(UserModelForm):
	class Meta:
		model = ControlSet
		fields = ['layout_name', 'notes', 'active']
		widgets = {
			'note': Textarea(attrs={'cols': 60, 'rows': 2}),
		}
		
class LysateBatchForm(UserModelForm):
	protocol = ExtractionProtocolSelect(queryset=ExtractionProtocol.objects.filter(active=True).order_by('-start_date'))
	control_set = ControlSetSelect(queryset=ControlSet.objects.filter(active=True).order_by('layout_name'))
	
	class Meta:
		model = LysateBatch
		fields = ['batch_name', 'protocol', 'control_set', 'date', 'robot', 'note', 'technician', 'status']
		widgets = {
			'note': Textarea(attrs={'cols': 60, 'rows': 2}),
		}
		
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		for option in ['protocol', 'date', 'robot']:
			self.fields[option].required = False
			
	def disable_fields(self):
		for field in LysateBatchForm._meta.fields:
			self.fields[field].disabled = True
			
class LysateForm(UserModelForm):
	well_position = forms.CharField(disabled=True)
	class Meta:
		model = Lysate
		fields = ['well_position', 'lysate_id', 'powder_used_mg', 'total_volume_produced', 'plate_id', 'barcode', 'notes']
		widgets = {
			'note': Textarea(attrs={'cols': 60, 'rows': 2}),
		}
	
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		for option in ['lysate_id']:
			self.fields[option].disabled = True
		if self.instance:
			layout_elements = self.instance.lysatebatchlayout_set
			layout_element = layout_elements.get(lysate=self.instance)
			self.initial['well_position'] = str(layout_element)
		
LysateFormset = modelformset_factory(Lysate, form=LysateForm, extra=0)

# raise validation error if extract batch name already exists
def validate_extract_batch_does_not_exist(extract_batch_name):
	try:
		extract_batch = ExtractionBatch.objects.get(batch_name=extract_batch_name)
		raise ValidationError(_('Extract Batch already exists: %(extract_batch_name)s'), 
						code='exists', 
						params={'extract_batch_name': extract_batch_name})
	except ExtractionBatch.DoesNotExist:
		pass

# 
class LysateBatchToExtractBatchForm(forms.Form):
	extract_batch_name = forms.CharField(max_length=50, label='Extract Batch name', validators=[validate_extract_batch_does_not_exist])
		
class ExtractionBatchForm(UserModelForm):
	protocol = ExtractionProtocolSelect(queryset=ExtractionProtocol.objects.filter(active=True).order_by('-start_date'))
	control_set = ControlSetSelect(queryset=ControlSet.objects.filter(active=True).order_by('layout_name'))
	
	class Meta:
		model = ExtractionBatch
		fields = ['batch_name', 'protocol', 'control_set', 'date', 'robot', 'note', 'technician', 'status']
		widgets = {
			'note': Textarea(attrs={'cols': 60, 'rows': 2}),
		}
		
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		for option in ['date', 'robot']:
			self.fields[option].required = False
			
	def disable_fields(self):
		for field in ExtractionBatchForm._meta.fields:
			self.fields[field].disabled = True
			
class ExtractForm(UserModelForm):
	well_position = forms.CharField(disabled=True)
	class Meta:
		model = Extract
		fields = ['well_position', 'extract_id', 'lysis_volume_extracted', 'notes']
		widgets = {
			'note': Textarea(attrs={'cols': 60, 'rows': 2}),
		}
	
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.fields['extract_id'].disabled = True
		
		if self.instance:
			layout_elements = self.instance.extractionbatchlayout_set
			layout_element = layout_elements.get(extract=self.instance)
			self.initial['well_position'] = str(layout_element)
		
ExtractFormset = modelformset_factory(Extract, form=ExtractForm, extra=0)
			
# raise validation error if library batch name already exists
def validate_library_batch_does_not_exist(library_batch_name):
	try:
		library_batch = LibraryBatch.objects.get(name=library_batch_name)
		raise ValidationError(_('Library Batch already exists: %(library_batch_name)s'), 
						code='exists', 
						params={'library_batch_name': library_batch_name})
	except LibraryBatch.DoesNotExist:
		pass
			
class ExtractBatchToLibraryBatchForm(forms.Form):
	library_batch_name = forms.CharField(max_length=50, label='Library Batch name', validators=[validate_library_batch_does_not_exist])
		
class ControlTypeSelect(ModelChoiceField):
	def label_from_instance(self, obj):
		return obj.control_type
		
class ControlTypeForm(UserModelForm):
	class Meta:
		fields = ['control_type']
		
ControlTypeFormset = modelformset_factory(ControlType, form=ControlTypeForm, max_num=20)

class ControlLayoutForm(UserModelForm):
	control_type = ControlTypeSelect(queryset=ControlType.objects.all())
	class Meta:
		model = ControlLayout
		fields = ['row', 'column', 'control_type', 'active']

ControlLayoutFormset = modelformset_factory(ControlLayout, form=ControlLayoutForm, extra=7)

LOST_ROW = 'H'
LOST_COLUMN = 6

class LostPowderForm(UserModelForm):
	powder_sample = ModelChoiceField(queryset=PowderSample.objects.all(), widget=TextInput, help_text='Powder Sample ID string', to_field_name='powder_sample_id')
	
	class Meta:
		model = LysateBatchLayout
		fields = ['powder_sample', 'powder_used_mg', 'notes', 'created_by']
		widgets = {
			'notes': Textarea(attrs={'cols': 60, 'rows': 2}),
		}
		
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		if self.instance.pk:
			#print(self.instance.powder_sample.powder_sample_id)
			self.initial.update({'powder_sample': self.instance.powder_sample.powder_sample_id})
		else:
			self.fields['powder_sample'].initial = None
		self.fields['created_by'].disabled = True
			
	def save(self, commit=True):
		lost_powder = super().save(commit=False)
		lost_powder.row = LOST_ROW
		lost_powder.column = LOST_COLUMN
		lost_powder.save()
		return lost_powder
		
LostPowderFormset = modelformset_factory(LysateBatchLayout, form=LostPowderForm)

class LostLysateForm(UserModelForm):
	lysate = ModelChoiceField(queryset=Lysate.objects.all(), widget=TextInput, help_text='Lysate ID string', to_field_name='lysate_id')
	
	class Meta:
		model = ExtractionBatchLayout
		fields = ['lysate', 'lysate_volume_used', 'notes', 'created_by']
		widgets = {
			'notes': Textarea(attrs={'cols': 60, 'rows': 2}),
		}
		
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		if self.instance.pk:
			self.initial.update({'lysate': self.instance.lysate.lysate_id})
		else:
			self.fields['lysate'].initial = None
		self.fields['created_by'].disabled = True
			
	def save(self, commit=True):
		lost_lysate = super().save(commit=False)
		lost_lysate.row = LOST_ROW
		lost_lysate.column = LOST_COLUMN
		lost_lysate.save()
		return lost_lysate

LostLysateFormset = modelformset_factory(ExtractionBatchLayout, form=LostLysateForm)

# to display the name instead of a primary key
class LibraryProtocolSelect(ModelChoiceField):
	def label_from_instance(self, obj):
		return obj.name
		
class LibraryProtocolForm(UserModelForm):
	class Meta:
		model = LibraryProtocol
		fields = ['name', 'start_date', 'end_date', 'description', 'manuscript_summary', 'protocol_reference', 'manual_robotic', 'volume_extract_used_standard', 'udg_treatment', 'library_type']

class LibraryBatchForm(UserModelForm):
	protocol = LibraryProtocolSelect(queryset=LibraryProtocol.objects.all())
	control_set = ControlSetSelect(queryset=ControlSet.objects.filter(active=True).order_by('layout_name'))
	
	class Meta:
		model = LibraryBatch
		fields = ['name', 'protocol', 'technician', 'prep_date', 'prep_note', 'prep_robot', 'cleanup_robot', 'qpcr_machine', 'control_set', 'p7_offset', 'status']
		widgets = {
			'prep_note': Textarea(attrs={'cols': 60, 'rows': 2}),
		}
		
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		for option in ['protocol', 'prep_date', 'prep_robot', 'p7_offset']:
			self.fields[option].required = False
	
	def disable_fields(self):
		for field in LibraryBatchForm._meta.fields:
			self.fields[field].disabled = True
			
# to display the name instead of a primary key
class BarcodeSelect(ModelChoiceField):
	def label_from_instance(self, obj):
		return obj.label
			
class LibraryForm(UserModelForm):
	p5_barcode = BarcodeSelect(queryset=Barcode.objects.all())
	p7_barcode = BarcodeSelect(queryset=Barcode.objects.all())
	
	class Meta:
		model = Library
		fields = ['reich_lab_library_id', 'p5_barcode', 'p7_barcode', 'nanodrop', 'qpcr', 'plate_id', 'position', 'barcode', 'notes']
		widgets = {
			'notes': Textarea(attrs={'cols': 60, 'rows': 2}),
		}
	
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.fields['reich_lab_library_id'].disabled = True
		for option in ['nanodrop', 'qpcr']:
			self.fields[option].required = False

LibraryFormset = modelformset_factory(Library, form=LibraryForm, extra=0)

# raise validation error if capture batch name already exists
def validate_capture_batch_does_not_exist(capture_batch_name):
	try:
		capture_batch = NuclearCapturePlate.objects.get(name=capture_batch_name)
		raise ValidationError(_('NuclearCapturePlate already exists: %(capture_batch_name)s'), 
						code='exists', 
						params={'capture_batch_name': capture_batch_name})
	except NuclearCapturePlate.DoesNotExist:
		pass
			
class LibraryBatchToCaptureBatchForm(forms.Form):
	capture_batch_name = forms.CharField(max_length=50, label='Capture Batch name', validators=[validate_capture_batch_does_not_exist])

class CaptureProtocolSelect(ModelChoiceField):
	def label_from_instance(self, obj):
		return obj.name

class CaptureBatchForm(UserModelForm):
	protocol = CaptureProtocolSelect(queryset=NuclearCaptureProtocol.objects.all())
	
	class Meta:
		model = NuclearCapturePlate
		fields = ['name', 'enrichment_type', 'protocol', 'technician', 'date', 'robot', 'hyb_wash_temps', 'p5_index_start', 'notes']
		widgets = {
			'notes': Textarea(attrs={'cols': 60, 'rows': 2}),
		}
	
	def disable_fields(self):
		for field in CaptureBatchForm._meta.fields:
			self.fields[field].disabled = True

class SpreadsheetForm(forms.Form):
	spreadsheet = forms.FileField(help_text='Retain headers from downloaded spreadsheet')
	
class StorageForm(UserModelForm):
	class Meta:
		model = Storage
		fields = ['equipment_type', 'equipment_location', 'equipment_name', 'shelf', 'rack', 'drawer', 'unit_name', 'unit_type']

StorageFormset = modelformset_factory(Storage, form=StorageForm)
