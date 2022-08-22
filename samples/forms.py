from django import forms
from django.forms import ModelChoiceField, ChoiceField, FileField, ModelForm, Textarea, IntegerField, CharField, BoundField, ValidationError, FloatField
from django.forms import modelformset_factory
from django.forms.widgets import TextInput, NumberInput
from django.utils.translation import gettext_lazy as _

from samples.models import PowderBatch, PowderSample, Sample, SamplePrepProtocol, ControlType, ControlSet, ControlLayout, LysateBatch, ExtractionProtocol, ExpectedComplexity, SamplePrepQueue, Lysate, LysateBatchLayout, ExtractionBatch, ExtractionBatchLayout, LibraryProtocol, LibraryBatch, Extract, Storage, Library, LibraryBatchLayout, P5_Index, P7_Index, Barcode, CaptureProtocol, CaptureOrShotgunPlate, CaptureLayout, SequencingPlatform, SequencingRun, SkeletalElementCategory, get_value

import datetime

class NativeDateInput(forms.widgets.DateInput):
	input_type = 'date'

class IndividualForm(forms.Form):
	individual_id = forms.IntegerField(label='Reich Lab Individual ID') 

class LibraryIDForm(forms.Form):
	library_id = forms.CharField(max_length=20, min_length=7, label='Reich Lab Library ID')

# This is basically a ModelForm with an additional user (Django login object) field for tracking who has modified objects in the save method
class UserModelForm(ModelForm):
	def __init__(self, *args, user, **kwargs):
		self.user = user
		super().__init__(*args, **kwargs)
		# Use the native HTML date picker instead of a text input
		for name, field in self.fields.items():
			if isinstance(field, forms.fields.DateField):
				field.widget = NativeDateInput()
		
	def save(self, commit=True):
		m = super().save(commit=False)
		m.save_user = self.user
		if commit:
			m.save()
		return m
	
	class Meta:
		abstract = True

class PowderBatchForm(UserModelForm):
	notes = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 2})) 
	class Meta:
		model = PowderBatch
		fields = ['name', 'date', 'technician', 'status', 'notes']
		
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		for option in ['date']:
			self.fields[option].required = False
		
	# to view fields without being able to modify prior to deletion
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

class SampleSelectByReichLabID(forms.Form):
	sample = ModelChoiceField(
		queryset=Sample.objects.all(),
		widget=NumberInput,
		help_text="Reich Lab Sample Number",
		to_field_name='reich_lab_id'
	)
	
class SampleSummaryLookupForm(forms.Form):
	sample = ModelChoiceField(
		queryset=Sample.objects.all(),
		widget=NumberInput,
		help_text="Reich Lab Sample Number",
		to_field_name='reich_lab_id',
		required=False
	)
	lysate = ModelChoiceField(
		queryset=Lysate.objects.all(),
		widget=TextInput,
		help_text='Lysate FluidX barcode',
		to_field_name='barcode',
		required=False
	)
	library = ModelChoiceField(
		queryset=Library.objects.all(),
		widget=TextInput,
		help_text='Library FluidX barcode',
		to_field_name='fluidx_barcode',
		required=False
	)
	collaborator_id = CharField(
		help_text='Collaborator ID for sample (skeletal code)',
		required=False
	)

class SkeletalElementCategorySelect(ModelChoiceField):
	def label_from_instance(self, obj):
		return obj.category
	
# base class for PowderSampleForm and LysateBatchLayoutForm
class PowderSampleSharedForm(UserModelForm):
	collaborator_id = CharField(disabled=True, help_text='Sample identification code assigned by the collaborator')
	num_photos = IntegerField(disabled=True)
	reich_lab_sample = CharField(disabled=True)
	
	skeletal_element_category = SkeletalElementCategorySelect(queryset=SkeletalElementCategory.objects.filter().order_by('sort_order'))
	shipment_id = CharField(disabled=True, required=False)
	group_label = CharField(disabled=True, required=False)
	notes = CharField(disabled=True, required=False)
	notes2 = CharField(disabled=True, required=False)
	location = CharField(disabled=True)
	sample_prep_protocol = SamplePrepProtocolSelect(queryset=SamplePrepProtocol.objects.all())
	
	class Meta:
		# the subclass will define the model
		fields = ['collaborator_id', 'num_photos', 'reich_lab_sample', 'skeletal_element_category', 'powder_sample_id', 'sampling_notes', 'total_powder_produced_mg', 'powder_used_mg', 'storage_location', 'shipment_id', 'group_label', 'notes', 'notes2', 'location', 'sample_prep_lab', 'sample_prep_protocol']
		widgets = {
            'sampling_notes': Textarea(attrs={'cols': 60, 'rows': 2}),
        }
		
	def get_sample(self):
		if self.instance.pk:
			if hasattr(self.instance, 'sample'): # instance is a PowderSample
				sample = self.instance.sample
				#self.fields['powder_used_mg'].disabled = True
			elif self.instance.powder_sample.sample: # instance is a LysateBatchLayout
				sample = self.instance.powder_sample.sample
			else:
				raise ValueError('No sample')
			return sample
		
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		if self.instance.pk:
			sample = self.get_sample()
			if sample:
				self.fields['reich_lab_sample'].initial = f'S{sample.reich_lab_id}'
			
				self.fields['num_photos'].initial = sample.num_existing_photos()
				
				self.fields['collaborator_id'].initial = sample.skeletal_code
				self.fields['skeletal_element_category'].initial = sample.skeletal_element_category
				self.fields['shipment_id'].initial = sample.shipment.shipment_name if sample.shipment else ''
				self.fields['group_label'].initial = sample.group_label
				self.fields['notes'].initial = sample.notes
				self.fields['notes2'].initial = sample.notes_2
				self.fields['location'].initial = f'{sample.locality} {get_value(sample.location, "country")}'
		self.fields['powder_sample_id'].disabled = True
		
	def save(self, commit=True):
		sample = self.get_sample()
		sample.skeletal_element_category = self.cleaned_data['skeletal_element_category']
		sample.save(save_user=self.user)
		return super().save(commit=commit)
		
class PowderSampleForm(PowderSampleSharedForm):
	
	class Meta(PowderSampleSharedForm.Meta):
		model = PowderSample
		
		fields = PowderSampleSharedForm.Meta.fields.copy()
		to_replace = fields.index('powder_used_mg') # if prepared powder for lysis is not needed for powders (rather than LysateBatchLayout), then we can remove this
		fields[to_replace] = 'powder_for_extract'
		
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		
PowderSampleFormset = modelformset_factory(PowderSample, form=PowderSampleForm, extra=0, max_num=200)

# Powder batches generate a lysate batch layout element for each powder sample
# This is separately weighed and stored for use in the next lysate batch
# 
class LysateBatchLayoutForm(PowderSampleSharedForm):
	# These put widgets in place for fields that are present for PowderSample but not LysateBatchLayout
	powder_sample_id = CharField(disabled=True, required=False)
	sampling_notes = CharField(disabled=True, required=False)
	
	total_powder_produced_mg = FloatField(min_value=0, required=False)
	storage_location = CharField(required=False, disabled=True)
	sample_prep_lab  = CharField(required=False, disabled=True)
	
	class Meta(PowderSampleSharedForm.Meta):
		model = LysateBatchLayout
		
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		# populate disabled fields from sample, powder_sample
		powder_sample = self.instance.powder_sample
		self.fields['powder_sample_id'].initial = powder_sample.powder_sample_id
		self.fields['sampling_notes'].initial = powder_sample.sampling_notes
		self.fields['total_powder_produced_mg'].initial = powder_sample.total_powder_produced_mg
		self.fields['storage_location'].initial = powder_sample.storage_location
		self.fields['sample_prep_lab'].initial = powder_sample.sample_prep_lab
		# For a powder sample, this is input. For LysateBatchLayout elements, this is read from powder sample
		self.fields['sample_prep_protocol'].initial = powder_sample.sample_prep_protocol
		self.fields['sample_prep_protocol'].required = False
		
	def save(self, commit=True):
		powder_sample = self.instance.powder_sample
		powder_sample.total_powder_produced_mg = self.cleaned_data['total_powder_produced_mg']
		powder_sample.save(save_user=self.user)
		return super().save(commit=commit)
		
PreparedPowderSampleFormset = modelformset_factory(LysateBatchLayout, form=LysateBatchLayoutForm, extra=0, max_num=200)
		
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
	protocol = ExtractionProtocolSelect(queryset=ExtractionProtocol.objects.filter(active=True).order_by('-start_date'), empty_label=None)
	control_set = ControlSetSelect(queryset=ControlSet.objects.filter(active=True).order_by('layout_name'), required=False)
	date = forms.DateField(required=False)
	
	class Meta:
		model = LysateBatch
		fields = ['batch_name', 'protocol', 'control_set', 'date', 'note', 'technician', 'status']
		widgets = {
			'note': Textarea(attrs={'cols': 60, 'rows': 2}),
		}
		
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		for option in ['protocol', 'date']:
			self.fields[option].required = False
			
	# to view fields without being able to modify prior to deletion
	def disable_fields(self):
		for field in LysateBatchForm._meta.fields:
			self.fields[field].disabled = True
			
class LysateForm(UserModelForm):
	well_position = forms.CharField(disabled=True)
	collaborator_id = forms.CharField(disabled=True, required=False)
	powder_batch_name = forms.CharField(disabled=True, required=False)
	class Meta:
		model = Lysate
		fields = ['well_position', 'lysate_id', 'collaborator_id', 'powder_batch_name', 'powder_used_mg', 'total_volume_produced', 'plate_id', 'barcode', 'notes']
		widgets = {
			'notes': Textarea(attrs={'cols': 60, 'rows': 2}),
		}
	
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		for option in ['lysate_id']:
			self.fields[option].disabled = True
		if self.instance:
			layout_elements = self.instance.lysatebatchlayout_set
			try:
				layout_element = layout_elements.get(lysate=self.instance)
				self.initial['well_position'] = str(layout_element)
			except Exception as e:
				print(self.instance.lysate_id)
				pass
			
			if self.instance.powder_sample:
				if self.instance.powder_sample.sample:
					self.initial['collaborator_id'] = self.instance.powder_sample.sample.skeletal_code
				if self.instance.powder_sample.powder_batch:
					self.initial['powder_batch_name'] =  self.instance.powder_sample.powder_batch.name
		
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
	rotated = forms.BooleanField(help_text='This batch is rotated 180 degrees', required=False)
		
class ExtractionBatchForm(UserModelForm):
	protocol = ExtractionProtocolSelect(queryset=ExtractionProtocol.objects.filter(active=True).order_by('-start_date'), empty_label=None)
	control_set = ControlSetSelect(queryset=ControlSet.objects.filter(active=True).order_by('layout_name'))
	date = forms.DateField(required=False)
	
	class Meta:
		model = ExtractionBatch
		fields = ['batch_name', 'protocol', 'control_set', 'date', 'robot', 'rotated', 'note', 'technician', 'status']
		widgets = {
			'note': Textarea(attrs={'cols': 60, 'rows': 2}),
		}
		
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		for option in ['date', 'robot']:
			self.fields[option].required = False
		for option in ['rotated']:
			self.fields[option].disabled = True
			
	# to view fields without being able to modify prior to deletion
	def disable_fields(self):
		for field in ExtractionBatchForm._meta.fields:
			self.fields[field].disabled = True
			
class ExtractForm(UserModelForm):
	well_position = forms.CharField(disabled=True)
	fluidx_barcode = forms.CharField(disabled=True, required=False)
	class Meta:
		model = Extract
		fields = ['well_position', 'extract_id', 'fluidx_barcode', 'lysis_volume_extracted', 'notes']
		widgets = {
			'notes': Textarea(attrs={'cols': 60, 'rows': 2}),
		}
	
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.fields['extract_id'].disabled = True
		
		if self.instance:
			layout_elements = self.instance.extractionbatchlayout_set
			layout_element = layout_elements.get(extract=self.instance)
			self.initial['well_position'] = str(layout_element)
			self.initial['fluidx_barcode'] = layout_element.lysate.barcode
		
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
	control_set = ControlSetSelect(queryset=ControlSet.objects.all())
	control_type = ControlTypeSelect(queryset=ControlType.objects.all())
	class Meta:
		model = ControlLayout
		fields = ['control_set', 'row', 'column', 'control_type', 'active', 'notes']
		widgets = {
			'notes': Textarea(attrs={'cols': 60, 'rows': 2}),
		}

ControlLayoutFormset = modelformset_factory(ControlLayout, form=ControlLayoutForm, extra=20)

LOST_ROW = None
LOST_COLUMN = None

class LostPowderForm(UserModelForm):
	powder_sample = ModelChoiceField(queryset=PowderSample.objects.all(), widget=TextInput, help_text='Powder Sample ID string', to_field_name='powder_sample_id')
	
	class Meta:
		model = LysateBatchLayout
		fields = ['powder_sample', 'powder_used_mg', 'is_lost', 'notes', 'created_by']
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
		self.fields['is_lost'].disabled = True
		self.fields['created_by'].disabled = True
			
	def save(self, commit=True):
		lost_powder = super().save(commit=False)
		lost_powder.row = LOST_ROW
		lost_powder.column = LOST_COLUMN
		lost_powder.is_lost = True
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
		fields = ['name', 'start_date', 'end_date', 'description', 'manuscript_summary', 'protocol_reference', 'manual_robotic', 'volume_extract_used_standard', 'udg_treatment', 'library_type', 'active']
		
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		for option in ['start_date', 'end_date', 'description', 'manuscript_summary', 'protocol_reference', 'manual_robotic', 'volume_extract_used_standard']:
			self.fields[option].required = False

class LibraryBatchForm(UserModelForm):
	protocol = LibraryProtocolSelect(queryset=LibraryProtocol.objects.filter(active=True), empty_label=None)
	prep_date = forms.DateField(required=False)
	cleanup_date = forms.DateField(required=False)
	control_set = ControlSetSelect(queryset=ControlSet.objects.filter(active=True).order_by('layout_name'))
	
	class Meta:
		model = LibraryBatch
		fields = ['name', 'protocol', 'technician', 'prep_date', 'prep_note', 'prep_robot', 'cleanup_robot', 'cleanup_person', 'cleanup_date', 'qpcr_machine', 'control_set', 'p7_offset', 'status', 'rotated']
		widgets = {
			'prep_note': Textarea(attrs={'cols': 60, 'rows': 2}),
		}
		
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		for option in ['prep_date', 'prep_robot']:
			self.fields[option].required = False
		for option in ['rotated']:
			self.fields[option].disabled = True
	
	# to view fields without being able to modify prior to deletion
	def disable_fields(self):
		for field in LibraryBatchForm._meta.fields:
			self.fields[field].disabled = True
			
# to display the name instead of a primary key
class BarcodeSelect(ModelChoiceField):
	def label_from_instance(self, obj):
		return obj.label
			
class LibraryForm(UserModelForm):
	well_position = forms.CharField(disabled=True)
	p5_barcode = BarcodeSelect(queryset=Barcode.objects.all())
	p7_barcode = BarcodeSelect(queryset=Barcode.objects.all())
	
	class Meta:
		model = Library
		fields = ['well_position', 'reich_lab_library_id', 'p5_barcode', 'p7_barcode', 'nanodrop', 'qpcr', 'plate_id', 'fluidx_barcode', 'notes']
		widgets = {
			'notes': Textarea(attrs={'cols': 60, 'rows': 2}),
		}
	
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.fields['reich_lab_library_id'].disabled = True
		for option in ['nanodrop', 'qpcr']:
			self.fields[option].required = False
		if self.instance:
			layout_elements = self.instance.librarybatchlayout_set
			layout_element = layout_elements.get(library=self.instance)
			self.initial['well_position'] = str(layout_element)

LibraryFormset = modelformset_factory(Library, form=LibraryForm, extra=0)

# raise validation error if capture batch name already exists
def validate_capture_batch_does_not_exist(capture_batch_name):
	try:
		capture_batch = CaptureOrShotgunPlate.objects.get(name=capture_batch_name)
		raise ValidationError(_('CaptureOrShotgunPlate already exists: %(capture_batch_name)s'), 
						code='exists', 
						params={'capture_batch_name': capture_batch_name})
	except CaptureOrShotgunPlate.DoesNotExist:
		pass
			
class LibraryBatchToCaptureBatchForm(forms.Form):
	capture_batch_name = forms.CharField(max_length=50, label='Capture Batch name', validators=[validate_capture_batch_does_not_exist])
	
class CaptureProtocolForm(UserModelForm):
	class Meta:
		model = CaptureProtocol
		fields = ['name', 'start_date', 'end_date', 'description', 'manuscript_summary', 'protocol_reference', 'active']
	
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		for option in ['start_date', 'end_date', 'description']:
			self.fields[option].required = False

class CaptureProtocolSelect(ModelChoiceField):
	def label_from_instance(self, obj):
		return obj.name

class CaptureBatchForm(UserModelForm):
	protocol = CaptureProtocolSelect(queryset=CaptureProtocol.objects.filter(active=True))
	date = forms.DateField(required=False)
	
	class Meta:
		model = CaptureOrShotgunPlate
		fields = ['name', 'protocol', 'technician', 'date', 'status', 'robot', 'hyb_wash_temps', 'p5_index_start', 'reagent_batch', 'needs_sequencing', 'notes']
		widgets = {
			'notes': Textarea(attrs={'cols': 60, 'rows': 2}),
		}
		
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		for option in ['date', 'robot', 'hyb_wash_temps', 'reagent_batch']:
			self.fields[option].required = False
	
	# to view fields without being able to modify prior to deletion
	def disable_fields(self):
		for field in CaptureBatchForm._meta.fields:
			self.fields[field].disabled = True
			
class CapturedLibraryForm(UserModelForm):
	well_position = forms.CharField(disabled=True)
	library_id = forms.CharField(disabled=True)
	library_batch = forms.CharField(disabled=True, required=False)
	well_position_library_batch = forms.CharField(disabled=True, required=False)
	p5_index = BarcodeSelect(queryset=P5_Index.objects.all(), disabled=True)
	p7_index = BarcodeSelect(queryset=P7_Index.objects.all(), disabled=True)
	p5_barcode = forms.CharField(disabled=True, required=False)
	p7_barcode = forms.CharField(disabled=True, required=False)
	class Meta:
		model = CaptureLayout
		fields = ['well_position', 'library_id', 'nanodrop', 'library_batch', 'well_position_library_batch', 'p5_index', 'p7_index', 'p5_barcode', 'p5_barcode']
		
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		for option in ['nanodrop']:
			self.fields[option].required = False
		if self.instance:
			self.initial['well_position'] = str(self.instance)
			if self.instance.library:
				self.initial['library_id'] = self.instance.library.reich_lab_library_id
				if self.instance.library.library_batch:
					self.initial['library_batch'] = self.instance.library.library_batch.name
					library_layout_element = LibraryBatchLayout.objects.get(library_batch=self.instance.library.library_batch, library=self.instance.library)
					self.initial['well_position_library_batch'] = str(library_layout_element)
				
				# library has indices, these override the layout element
				if self.instance.library.p5_index:
					self.initial['p5_index'] = self.instance.library.p5_index
				if self.instance.library.p7_index:
					self.initial['p7_index'] = self.instance.library.p7_index
				
				self.initial['p5_barcode'] = get_value(self.instance.library.p5_barcode, 'label')
				self.initial['p7_barcode'] = get_value(self.instance.library.p7_barcode, 'label')
			elif self.instance.control_type:
				self.initial['library_id'] = self.instance.control_type.control_type
		
CapturedLibraryFormset = modelformset_factory(CaptureLayout, form=CapturedLibraryForm, extra=0)
			
# raise validation error if sequencing run name already exists
def validate_sequencing_run_does_not_exist(sequencing_run_name):
	try:
		sequencing_run = SequencingRun.objects.get(name=sequencing_run_name)
		raise ValidationError(_('SequencingRun already exists: %(sequencing_run_name)s'), 
						code='exists', 
						params={'sequencing_run_name': sequencing_run_name})
	except SequencingRun.DoesNotExist:
		pass
			
class CaptureBatchToSequencingRunForm(forms.Form):
	sequencing_run_name = forms.CharField(max_length=50, label='Sequencing run name', validators=[validate_sequencing_run_does_not_exist])
			
class SequencingPlatformSelect(ModelChoiceField):
	def label_from_instance(self, obj):
		return f'{obj}'
		
class SequencingPlatformForm(UserModelForm):
	class Meta:
		model = SequencingPlatform
		fields = ['platform', 'note', 'location', 'active']
		
class SequencingRunForm(UserModelForm):
	sequencing = SequencingPlatformSelect(queryset=SequencingPlatform.objects.filter(active=True).order_by('-id'))
	date_pooled = forms.DateField(required=False)
	
	class Meta:
		model = SequencingRun
		fields = ['name', 'technician', 'sequencing', 'notes', 'read_length', 'lanes_estimated', 'lanes_sequenced', 'date_pooled', 'date_ready_for_sequencing', 'date_submitted_for_sequencing', 'date_data_available', 'date_analysis_started', 'date_analysis_complete', 'date_ready_for_pulldown', 'date_pulldown_complete', 'reich_lab_release_version',]
	
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		for option in ['sequencing', 'read_length', 'lanes_estimated', 'lanes_sequenced', 'date_ready_for_sequencing', 'date_submitted_for_sequencing', 'date_data_available', 'date_analysis_started', 'date_analysis_complete', 'date_ready_for_pulldown', 'date_pulldown_complete', 'reich_lab_release_version',]:
			self.fields[option].required = False
		
	# to view fields without being able to modify prior to deletion
	def disable_fields(self):
		for field in SequencingRunForm._meta.fields:
			self.fields[field].disabled = True

class SpreadsheetForm(forms.Form):
	spreadsheet = forms.FileField(help_text='Retain headers from downloaded spreadsheet')
	
class BatchUploadForm(forms.Form):
	spreadsheet = forms.FileField(help_text='"Library" and "Position" header')
	
class StorageForm(UserModelForm):
	class Meta:
		model = Storage
		fields = ['equipment_type', 'equipment_location', 'equipment_name', 'shelf', 'rack', 'drawer', 'unit_name', 'unit_type']

StorageFormset = modelformset_factory(Storage, form=StorageForm)

