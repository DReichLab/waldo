from django.db import models
from django.utils import timezone
from datetime import date

from django.contrib.auth.models import User

from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.utils.translation import gettext_lazy as _

from django.db.models import Max

import re, string

def parse_sample_string(s):
	# we expect a sample number to start with 'S'
	# S1234a
	match = re.fullmatch('S([\d]+)([a-z]?)', s)
	if match:
		sample_number = int(match.group(1))
		control = match.group(2)
		return sample_number, control
	else:
		raise ValueError('Error parsing sample {}'.format(s))

class Timestamped(models.Model):
	creation_timestamp = models.DateTimeField(default=timezone.now, null=True)
	created_by = models.CharField(max_length=20, blank=True)
	modification_timestamp = models.DateTimeField(default=timezone.now, null=True)
	modified_by = models.CharField(max_length=20, blank=True)
	
	class Meta:
		abstract = True
	
	# save_user is a Django User object
	def save(self, *args, **kwargs):
		if 'save_user' in kwargs:
			save_user = kwargs.pop('save_user')
		else:
			save_user = getattr(self, 'save_user', None)
		current_time = timezone.now()
		if save_user is not None:
			self.modified_by = save_user.username
			if self.pk is None:
				self.created_by = save_user.username
				self.creation_timestamp = current_time
		self.modification_timestamp = current_time
		super(Timestamped, self).save(*args, **kwargs)


PLATE_ROWS = 'ABCDEFGH'
		
def validate_row_letter(letter):
	if len(letter) != 1:
		raise ValidationError(
			_('Row letter %(letter)s must be 1 character.'),
			params={'letter': letter},
		)
	if letter not in PLATE_ROWS:
		raise ValidationError(
			_('Row letter %(letter)s is out of allowed A-H range.'),
			params={'letter': letter},
		)

# column first, then row (A1, B1, ..., H1, A2)
def plate_location(int_val):
	row_index = int_val % 8
	column_index = int_val / 8 + 1
	return PLATE_ROWS[row_index], column_index
		
class TimestampedWellPosition(Timestamped):
	row = models.CharField(max_length=1, validators=[validate_row_letter])
	column = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(12)])
	
	class Meta:
		abstract = True
		
	def same_position(self, other_position):
		return self.row == other_position.row and self.column == other_position.column
	
	def set_position(self, position_string):
		self.row = position_string[0]
		self.column = int(position_string[1:])
	
	def __str__(self):
		return f'{self.row}{self.column}'

class Shipment(Timestamped):
	shipment_name = models.CharField(max_length=30, db_index=True, unique=True)
	arrival_date = models.DateField(null=True)
	arrival_method = models.CharField(max_length=255, blank=True)
	tracking_number = models.CharField(max_length=30, blank=True)
	arrival_notes = models.TextField(blank=True)
	shipment_notes = models.TextField(blank=True)
	documents_location = models.TextField(blank=True)
	additional_information_location = models.TextField(blank=True)
	
class Collaborator(Timestamped):
	first_name = models.CharField(max_length=50, db_index=True)
	last_name = models.CharField(max_length=50, db_index=True)
	title = models.CharField(max_length=65, help_text="Collaborator's professional title", blank=True)
	institution = models.CharField(max_length=100, db_index=True, help_text="Collaborator's associated institution or company", blank=True)
	department = models.CharField(max_length=110, help_text="Collaborator's department or division", blank=True)
	address_1 = models.CharField(max_length=70, blank=True)
	address_2 = models.CharField(max_length=50, blank=True)
	address_3 = models.CharField(max_length=50, blank=True)
	city = models.CharField(max_length=50, blank=True)
	county_region = models.CharField(max_length=50, blank=True)
	state = models.CharField(max_length=50, blank=True)
	country = models.CharField(max_length=50, db_index=True, blank=True)
	postal_code = models.CharField(max_length=20, blank=True)
	phone_number_office = models.CharField(max_length=30, blank=True)
	phone_number_mobile = models.CharField(max_length=30, blank=True)
	email_1 = models.CharField(max_length=50, blank=True)
	email_2 = models.CharField(max_length=50, blank=True)
	skype_user_name = models.CharField(max_length=30, blank=True)
	facetime_user_name = models.CharField(max_length=30, blank=True)
	whatsapp_user_name = models.CharField(max_length=30, blank=True)
	twitter = models.CharField(max_length=50, blank=True)
	facebook = models.CharField(max_length=50, blank=True)
	website = models.CharField(max_length=200, blank=True)
	research_gate_academia = models.CharField(max_length=100, blank=True)
	notes = models.TextField(help_text='Additional information about collaborator', blank=True)
	
	primary_collaborator = models.BooleanField(null=True, db_index=True, help_text='Is this person a Primary Collaborator? This field is used select collaborators for Harvard office of Academic Reasearch Integrity approval')
	ora_approval = models.BooleanField(db_index=True, help_text='Has the Harvard office of Academic Research Integrity cleared this collaborator?', default=False)
	
class Publication(Timestamped):
	title = models.CharField(max_length=200)
	first_author = models.CharField(max_length=50, blank=True)
	year = models.PositiveSmallIntegerField(null=True)
	journal = models.CharField(max_length=100, blank=True)
	pages = models.CharField(max_length=30, blank=True)
	author_list = models.TextField(blank=True)
	url = models.CharField(max_length=50, blank=True)

class WetLabStaff(Timestamped):
	first_name = models.CharField(max_length=30, db_index=True)
	last_name = models.CharField(max_length=30, db_index=True)
	start_date = models.DateField(null=True)
	end_date = models.DateField(null=True)
	title = models.CharField(max_length=50, blank=True)
	email_1 = models.CharField(max_length=50, blank=True)
	email_2 = models.CharField(max_length=50, blank=True)
	phone_number = models.CharField(max_length=30, blank=True)
	
	login_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
	
	def initials(self):
		return self.first_name[0] + self.last_name[0]
	
class SupportStaff(Timestamped):
	first_name = models.CharField(max_length=30, db_index=True)
	last_name = models.CharField(max_length=30, db_index=True)
	start_date = models.DateField(null=True)
	end_date = models.DateField(null=True)
	title = models.CharField(max_length=50, blank=True)
	email_1 = models.CharField(max_length=50, blank=True)
	email_2 = models.CharField(max_length=50, blank=True)
	phone_number = models.CharField(max_length=30, blank=True)
	
class Return(Timestamped):
	collaborator = models.ForeignKey(Collaborator, on_delete=models.PROTECT)
	return_date = models.DateField(default=date.today)
	return_method = models.CharField(max_length=50, blank=True)
	tracking_number = models.CharField(max_length=30, blank=True)
	courier_delivery_date = models.DateField(null=True)
	return_notes = models.TextField(blank=True)
	
class Country(Timestamped):
	country_name = models.CharField(max_length=100, blank=True)
	region = models.CharField(max_length=100, blank=True)
	subregion = models.CharField(max_length=100, blank=True)
	intermediate_region = models.CharField(max_length=100, blank=True)
	m49_code = models.PositiveSmallIntegerField(null=True)
	iso_alpha2_code = models.CharField(max_length=2, blank=True)
	iso_alpha3_code = models.CharField(max_length=3, blank=True)

class Location(Timestamped):
	country = models.ForeignKey(Country, on_delete=models.PROTECT, null=True)
	level_1 = models.CharField(max_length=100, blank=True) # coarsest
	level_2 = models.CharField(max_length=100, blank=True)
	level_3 = models.CharField(max_length=100, blank=True)
	level_4 = models.CharField(max_length=100, blank=True)
	level_5 = models.CharField(max_length=100, blank=True) # finest
	site = models.TextField(blank=True)
	latitude = models.CharField(max_length=20, blank=True) # TODO convert to spatial
	longitude = models.CharField(max_length=20, blank=True) # TODO
	
class Period(Timestamped):
	abbreviation = models.CharField(max_length=50)
	text = models.TextField(blank=True)
	description = models.TextField(blank=True)
	date_range = models.CharField(max_length=50, blank=True)
	
class Culture(Timestamped):
	abbreviation = models.CharField(max_length=50)
	text = models.TextField(blank=True)
	description = models.TextField(blank=True)
	date_range = models.CharField(max_length=50, blank=True)
	
class Storage(Timestamped):
	equipment_type = models.CharField(max_length=50, blank=True)
	equipment_location = models.CharField(max_length=50, blank=True)
	equipment_name = models.CharField(max_length=50, blank=True)
	shelf = models.PositiveSmallIntegerField(null=True)
	rack = models.PositiveSmallIntegerField(null=True)
	drawer = models.PositiveSmallIntegerField(null=True)
	unit_name = models.CharField(max_length=50, blank=True)
	unit_type = models.CharField(max_length=50, blank=True)
	
# Samples are sequenced in batches with similar expected complexity to prevent more complex samples from overwhelming less complex samples
class ExpectedComplexity(models.Model):
	description = models.CharField(max_length=50, unique=True)
	sort_order = models.SmallIntegerField()
	
CONTROL_CHARACTERS = string.ascii_lowercase

class Sample(Timestamped):
	reich_lab_id = models.PositiveIntegerField(db_index=True, null=True, help_text=' assigned when a sample is selected from the queue by the wetlab')
	control = models.CharField(max_length=1, blank=True, help_text='Non-empty value indicates this is a control')
	queue_id = models.PositiveIntegerField(db_index=True, unique=True, null=True)
	
	collaborator = models.ForeignKey(Collaborator, on_delete=models.PROTECT, null=True)
	shipment = models.ForeignKey(Shipment, on_delete=models.PROTECT, null=True)
	return_id = models.ForeignKey(Return, on_delete=models.PROTECT, null=True)
	
	country_fk = models.ForeignKey(Country, on_delete=models.SET_NULL, null=True)
	location_fk = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True)
	periods = models.ManyToManyField(Period)
	cultures = models.ManyToManyField(Culture)
	publications = models.ManyToManyField(Publication)

	individual_id = models.CharField(max_length=15, blank=True)
	
	skeletal_element = models.CharField(max_length=50, blank=True, help_text='Type of bone sample submitted for aDNA analysis')
	skeletal_code = models.CharField(max_length=150, blank=True, help_text='Sample identification code assigned by the collaborator')
	skeletal_code_renamed = models.TextField(blank=True, help_text='Sample identification code assigned by the Reich Lab')
	sample_date = models.TextField(blank=True, help_text='Age of sample; either a radiocarbon date or a date interval.')
	average_bp_date = models.FloatField(null=True, help_text='Average Before Present date, calculated from average of calibrated date range after conversion to BP dates')
	date_fix_flag = models.TextField(help_text='Flag for any issues with the date information submitted by the collaborator', blank=True)
	group_label = models.CharField(max_length=100, blank=True, help_text='Country_Culture_Period of Individual')
	geo_region = models.CharField(max_length=50, blank=True, help_text='Geographic region component of group label of an Individual')
	geo_subregion = models.CharField(max_length=50, blank=True, help_text='Geographic subregion component of group label of an Individual')
	period = models.CharField(max_length=50, blank=True, help_text='Archaeologic period component of group label of an Individual')
	culture = models.CharField(max_length=50, blank=True, help_text='Archaeologic culture component of group label of an Individual')
	outlier = models.CharField(max_length=50, blank=True, help_text='Outlier designation component of group label of an Individual')
	locality = models.CharField(max_length=150, blank=True, help_text='Location where skeletal remains were found')
	country = models.CharField(max_length=30, blank=True, help_text='Country where skeletal remains were found')
	latitude = models.CharField(max_length=20, blank=True, help_text='Latitude where skeletal remains were found') # TODO convert to spatial
	longitude = models.CharField(max_length=20, blank=True, help_text='Longitude where skeletal remains were found') # TODO
	notes = models.TextField(blank=True, help_text='Any notes from the collaborator about the individual, sample, site, etc.')
	notes_2 = models.TextField(blank=True, help_text='Any notes from the collaborator about the individual, sample, site, etc.')
	collaborators = models.TextField(max_length=300, blank=True, help_text='List of additional collaborators asociated with the sample or reference if sample has been published') # convert to many-to-many field
	morphological_sex = models.CharField(max_length=20, blank=True, help_text='Sex as determined by skeletal remains') # TODO enumerated? 
	morphological_age = models.CharField(max_length=25, blank=True, help_text='Age as determined by skeletal remains: adult, child, infant, etc.') # TODO enumerated?
	morphological_age_range = models.CharField(max_length=15, blank=True, help_text='Age range in years as determined by skeletal remains') # TODO map to interval 
	loan_expiration_date = models.DateField(null=True, help_text='Date by which samples need to be returned to collaborator')
	dating_status = models.TextField(blank=True, help_text="David Reich's radiocarbon dating status as noted in his anno file") # TODO enumerate?
	
	burial_code = models.TextField(blank=True)
	accession_number = models.TextField(blank=True)
	pathology = models.TextField(blank=True)
	
	expected_complexity = models.ForeignKey(ExpectedComplexity, on_delete=models.SET_NULL, null=True)
	
	class Meta:
		unique_together = ['reich_lab_id', 'control']
		
	def assign_reich_lab_sample_number(self, **kwargs):
		if self.reich_lab_id is None:
			max_sample_number = Sample.objects.all().aggregate(Max('reich_lab_id'))['reich_lab_id__max']
			next_sample_number = max_sample_number + 1
			self.reich_lab_id = next_sample_number
			self.save(**kwargs)
		return self.reich_lab_id
	
	def is_control(self):
		return len(self.control) > 0
	
	def __str__(self):
		return f'S{self.reich_lab_id:04d}{self.control}'
		
class SamplePrepProtocol(Timestamped):
	preparation_method = models.CharField(max_length=50, help_text='Method used to produce bone powder')
	manuscript_summary = models.TextField(blank=True, help_text='Sampling method summary for manuscripts')
	protocol_reference = models.TextField(blank=True, help_text='Protocol citation')
	notes = models.TextField(blank=True, help_text='Notes about the method used to create bone powder')
	
class PowderBatchStatus(models.Model):
	description = models.CharField(max_length=50, unique=True)
	sort_order = models.SmallIntegerField()
	
class PowderBatch(Timestamped):
	name = models.CharField(max_length=50, unique=True)
	date = models.DateField(null=True)
	technician = models.CharField(max_length=50, blank=True)
	technician_fk = models.ForeignKey(WetLabStaff, on_delete=models.SET_NULL, null=True)
	status = models.ForeignKey(PowderBatchStatus, null=True, on_delete=models.SET_NULL)
	notes = models.TextField(blank=True)

class PowderSample(Timestamped):
	powder_sample_id = models.CharField(max_length=15, unique=True, null=False, db_index=True)
	sample = models.ForeignKey(Sample, on_delete=models.PROTECT, help_text='Powder was produced from this sample')
	powder_batch = models.ForeignKey(PowderBatch, on_delete=models.PROTECT, help_text='powder belongs to this processing batch', null=True)
	storage = models.ForeignKey(Storage, on_delete=models.PROTECT, null=True)
	
	sampling_tech = models.CharField(max_length=15, blank=True, help_text='Technique used to produce the bone powder')
	sampling_notes = models.TextField(help_text='Notes from technician about sample quality, method used, mg of bone powder produced and storage location', blank=True)
	total_powder_produced_mg = models.FloatField(null=True, help_text='Total milligrams of bone powder produced from the sample')
	powder_for_extract = models.FloatField(default=0, help_text='Milligrams of powder used for extract') # This is stored here temporarily as it is more properly a property of the extract.
	storage_location = models.CharField(max_length=50, blank=True, help_text='Storage location of remaining bone powder')
	sample_prep_lab = models.CharField(max_length=50, blank=True, help_text='Name of lab where bone powder was produced')
	sample_prep_protocol = models.ForeignKey(SamplePrepProtocol, on_delete=models.SET_NULL, null=True)
	
	def is_control(self):
		return powder_sample_id.endswith('NP')
	
# Wetlab consumes samples from this queue for powder batches
class SamplePrepQueue(Timestamped):
	priority = models.SmallIntegerField(help_text='Lower is higher priority')
	sample = models.ForeignKey(Sample, on_delete=models.CASCADE)
	sample_prep_protocol = models.ForeignKey(SamplePrepProtocol, on_delete=models.SET_NULL, null=True)
	udg_treatment = models.CharField(max_length=10)
	powder_batch = models.ForeignKey(PowderBatch, null=True, on_delete=models.SET_NULL,)
	powder_sample = models.ForeignKey(PowderSample, null=True, on_delete=models.SET_NULL) # needed to unassign
	
class ExtractionProtocol(Timestamped):
	name = models.CharField(max_length=150)
	start_date = models.DateField(null=True, blank=True)
	end_date = models.DateField(null=True, blank=True)
	description = models.TextField(blank=True)
	manual_robotic = models.CharField(max_length=20, blank=True)
	total_lysis_volume = models.FloatField(null=True, blank=True)
	lysate_fraction_extracted = models.FloatField(null=True, blank=True)
	final_extract_volume = models.FloatField(null=True, blank=True)
	binding_buffer = models.CharField(max_length=20, blank=True)
	manuscript_summary = models.CharField(max_length=150, blank=True)
	protocol_reference = models.TextField(blank=True)
	
	
# enumeration of the control types
class ControlType(models.Model):
	control_type = models.CharField(max_length=25, unique=True)

# each control layout comprises rows with the same name
# a control layout is applied to batch layouts to add controls
class ControlLayout(TimestampedWellPosition):
	layout_name = models.CharField(max_length=25, db_index=True)
	control_type = models.ForeignKey(ControlType, on_delete=models.PROTECT)
	active = models.BooleanField(default=True)

EXTRACT_NEGATIVE = 'Extract Negative'
LIBRARY_NEGATIVE = 'Library Negative'
LIBRARY_POSITIVE = 'Library Positive'

class ExtractBatch(Timestamped):
	batch_name = models.CharField(max_length=50, unique=True)
	protocol = models.ForeignKey(ExtractionProtocol, on_delete=models.PROTECT, null=True)
	technician = models.CharField(max_length=50, blank=True)
	technician_fk = models.ForeignKey(WetLabStaff, on_delete=models.SET_NULL, null=True)
	date = models.DateField(null=True, help_text='YYYY-MM-DD')
	robot = models.CharField(max_length=20, blank=True)
	note = models.TextField(blank=True)
	powder_batches = models.ManyToManyField(PowderBatch)
	layout = models.ManyToManyField(PowderSample, through='ExtractBatchLayout', related_name='powder_sample_assignment')
	control_layout_name = models.CharField(max_length=25, blank=True, help_text='When applying a layout, use this set of controls.  The control entries are stored in layout.')
	
	# count the number of samples in powder batches for this extract batch
	def num_powder_samples(self):
		num_powder_samples_assigned = 0
		for powder_batch in self.powder_batches.all():
			num_powder_samples_assigned += PowderSample.objects.filter(powder_batch=powder_batch).count()
		return num_powder_samples_assigned
	
	# assign a layout, one powder sample or control per position
	# this is the layout to produce lysate
	def assign_layout(self, user):
		control_types = [EXTRACT_NEGATIVE, LIBRARY_NEGATIVE, LIBRARY_POSITIVE]
		powders = ExtractBatchLayout.objects.filter(extract_batch=self, control_type=None).order_by('powder_sample__powder_batch', 'powder_sample__sample__reich_lab_id')
		controls = ControlLayout.objects.filter(layout_name=self.control_layout_name, control_type__control_type__in=control_types, active=True)
		# check count
		if powders.count() + controls.count() > 96:
			raise ValueError(f'Too many items for extract layout: {powders.count} powders and {controls.count} controls')
		
		count = 0
		# get existing controls
		existing_controls = ExtractBatchLayout.objects.filter(extract_batch=self, control_type__isnull=False).order_by('row', 'column')
		# we should check the existing controls for sample ids
		# Extract Negative: find the Reich lab sample ID used for extract negatives for this extract batch
		extract_negative_sample_id = None
		extract_negative_controls = existing_controls.filter(control_type__control_type=EXTRACT_NEGATIVE)
		for extract_negative_layout in extract_negative_controls:
			if extract_negative_sample_id is None:
				extract_negative_sample_id = extract_negative_layout.powder_sample.sample.reich_lab_id
			elif extract_negative_sample_id != extract_negative_layout.powder_sample.sample.reich_lab_id:
				raise ValueError(f'Multiple extract negative control sample ids: {extract_negative_sample_id} {extract_negative_layout.powder_sample.sample.reich_lab_id:}')
		# Library Negative: find the Reich lab sample ID used for library negatives for this extract batch
		library_negative_sample_id = None
		library_negative_controls = existing_controls.filter(control_type__control_type=LIBRARY_NEGATIVE)
		for library_negative_layout in library_negative_controls:
			if library_negative_sample_id is None:
				library_negative_sample_id = library_negative_layout.powder_sample.sample.reich_lab_id
			elif library_negative_sample_id != library_negative_layout.powder_sample.sample.reich_lab_id:
				raise ValueError(f'Multiple library negative control sample ids: {library_negative_sample_id} {library_negative_layout.powder_sample.sample.reich_lab_id:}')
		# remove existing control layout entries
		for existing_control in existing_controls:
			existing_control.destroy_control(user)
			existing_control.delete()
		# create new control layout entries
		extract_negative_control_count = 0
		library_negative_control_count = 0
		for control in controls:
			layout_element = ExtractBatchLayout(extract_batch=self, control_type=control.control_type, row=control.row, column=control.column, powder_used_mg=0)
			# create sample and powder sample
			control_type = control.control_type.control_type
			if layout_element.powder_sample is None and control_type != LIBRARY_POSITIVE:
				control_sample_id = None
				if control_type == EXTRACT_NEGATIVE:
					control_character = CONTROL_CHARACTERS[extract_negative_control_count]
					extract_negative_control_count += 1
					if extract_negative_sample_id is not None:
						control_sample_id = extract_negative_sample_id
				elif control_type == LIBRARY_NEGATIVE:
					control_character = CONTROL_CHARACTERS[library_negative_control_count]
					library_negative_control_count += 1
					if library_negative_sample_id is not None:
						control_sample_id = library_negative_sample_id
				else:
					raise ValueError(f'{control_type}')
				control_sample = Sample(control=control_character)
				if control_sample_id is not None:
					control_sample.reich_lab_id = control_sample_id
					control_sample.save(save_user=user)
				else:
					reich_lab_sample_id = control_sample.assign_reich_lab_sample_number(save_user=user)
					# use this sample ID for later controls of same type
					if control_type == EXTRACT_NEGATIVE:
						extract_negative_sample_id = reich_lab_sample_id
					elif control_type == LIBRARY_NEGATIVE:
						library_negative_sample_id = reich_lab_sample_id
					else:
						raise ValueError(f'{control_type}')
				
				powder_sample_control = PowderSample(sample=control_sample, powder_sample_id=f'{str(control_sample)}.NP')
				powder_sample_control.save(save_user=user)
				layout_element.powder_sample = powder_sample_control
					
			layout_element.save(save_user=user)
		for layout_element in powders:
			# check positions until there is no control
			while True:
				row, column = plate_location(count)
				position = {'row': row, 'column': column}
				layout_element.row = row
				layout_element.column = column
				count += 1
				# if this position is occupied by a control, then move to the next position
				control_free_position = True
				for control in controls:
					if control.same_position(layout_element):
						control_free_position = False
						break
				# if there is no control in this position, we are done with this powder
				if control_free_position:
					break
			layout_element.save(save_user=user)

# 
class ExtractBatchLayout(TimestampedWellPosition):
	extract_batch = models.ForeignKey(ExtractBatch, on_delete=models.CASCADE, null=True) # use a null extract batch to mark lost powder
	powder_sample = models.ForeignKey(PowderSample, on_delete=models.CASCADE, null=True)
	control_type = models.ForeignKey(ControlType, on_delete=models.PROTECT, null=True)
	powder_used_mg = models.FloatField()
	
	def destroy_control(self, user):
		if self.control_type is not None:
			if self.powder_sample is not None:
				to_delete_powder_sample = self.powder_sample
				self.powder_sample = None
				to_delete_sample = to_delete_powder_sample.sample
				if not to_delete_powder_sample.is_control():
					raise ValueError(f'{to_delete_powder_sample.powder_sample_id} does not appear to be a control')
				if not to_delete_sample.is_control():
					raise ValueError(f'{to_delete_sample.powder_sample_id} does not appear to be a control')
				to_delete_powder_sample.delete()
				to_delete_sample.delete()
				self.save(save_user=user)

class Lysate(Timestamped):
	lysate_id = models.CharField(max_length=15, unique=True, null=False, db_index=True)
	reich_lab_lysate_number = models.PositiveIntegerField(null=True, help_text='Starts at 1 for each sample.')
	powder_sample = models.ForeignKey(PowderSample, null=True, on_delete=models.PROTECT)
	storage = models.ForeignKey(Storage, on_delete=models.PROTECT, null=True)
	
	powder_used_mg = models.FloatField(null=True, help_text='milligrams of bone powder used in lysis')
	total_volume_produced = models.FloatField(null=True, help_text='Total microliters of lysate produced')
	
	plate_id = models.CharField(max_length=12, blank=True, help_text='FluidX rack barcode')
	position = models.CharField(max_length=3, blank=True, help_text='well/tube position in plate/rack')
	barcode = models.CharField(max_length=12, blank=True, help_text='Physical barcode on FluidX tube')
	notes = models.TextField(blank=True)
	
class Extract(Timestamped):
	extract_id = models.CharField(max_length=20, unique=True, db_index=True)
	reich_lab_extract_number = models.PositiveIntegerField(null=True, help_text='Starts at 1 for each lysate or sample if no lysate exists.')
	lysate = models.ForeignKey(Lysate, on_delete=models.PROTECT, null=True)
	sample = models.ForeignKey(Sample, on_delete=models.PROTECT, null=True)
	extract_batch = models.ForeignKey(ExtractBatch, null=True, on_delete=models.PROTECT)
	storage = models.ForeignKey(Storage, on_delete=models.PROTECT, null=True)
	lysis_volume_extracted = models.FloatField(null=True)
	#extract_volume_remaining = models.FloatField(null=True)
	notes = models.TextField(blank=True)
	storage_location = models.TextField(blank=True)
	extraction_lab = models.CharField(max_length=50, blank=True, help_text='Name of lab where DNA extraction was done')
	
class LibraryProtocol(Timestamped):
	name = models.CharField(max_length=50, unique=True)
	start_date = models.DateField(null=True)
	end_date = models.DateField(null=True)
	description = models.TextField(blank=True)
	manuscript_summary = models.CharField(max_length=50, blank=True)
	protocol_reference = models.TextField(blank=True)
	manual_robotic = models.CharField(max_length=20, blank=True)
	volume_extract_used_standard = models.FloatField(null=True)

class LibraryBatch(Timestamped):
	name = models.CharField(max_length=150, blank=True)
	protocol = models.ForeignKey(LibraryProtocol, on_delete=models.PROTECT, null=True)
	technician = models.CharField(max_length=50, blank=True)
	prep_date = models.DateField(null=True)
	prep_note = models.TextField(blank=True)
	prep_robot = models.CharField(max_length=20, blank=True)
	technician_fk = models.ForeignKey(WetLabStaff, on_delete=models.SET_NULL, null=True)
	
class Library(Timestamped):
	sample = models.ForeignKey(Sample, on_delete=models.PROTECT, null=True)
	extract = models.ForeignKey(Extract, on_delete=models.PROTECT, null=True)
	library_batch = models.ForeignKey(LibraryBatch, on_delete=models.PROTECT, null=True)
	reich_lab_library_id = models.CharField(max_length=20, unique=True, db_index=True)
	reich_lab_library_number = models.PositiveIntegerField(null=True, help_text='Starts at 1 for each extract or sample')
	udg_treatment = models.CharField(max_length=10)
	library_type = models.CharField(max_length=10, blank=True)
	library_prep_lab = models.CharField(max_length=50, blank=True, help_text='Name of lab where library preparation was done')
	ul_extract_used = models.FloatField(null=True)
	# mg_equivalent_powder_used
	alt_category = models.CharField(max_length=20, blank=True)
	notes = models.TextField(blank=True)
	assessment = models.TextField(blank=True, help_text='Xcontam listed if |Z|>2 standard errors from zero: 0.02-0.05="QUESTIONABLE", >0.05="QUESTIONABLE_CRITICAL" or "FAIL") (mtcontam 97.5th percentile estimates listed if coverage >2: <0.8 is "QUESTIONABLE_CRITICAL", 0.8-0.95 is "QUESTIONABLE", and 0.95-0.98 is recorded but "PASS", gets overriden by ANGSD')
	
	storage = models.ForeignKey(Storage, on_delete=models.PROTECT, null=True)
	plate_id = models.CharField(max_length=12, blank=True, help_text='FluidX rack barcode')
	position = models.CharField(max_length=3, blank=True, help_text='well/tube position in plate/rack')
	barcode = models.CharField(max_length=12, blank=True, help_text='Physical barcode on FluidX tube')
	
	nanodrop = models.FloatField(null=True)
	qpcr = models.FloatField(null=True)
	
class MTCaptureProtocol(Timestamped):
	name = models.CharField(max_length=150)
	start_date = models.DateField(null=True)
	end_date = models.DateField(null=True)
	description = models.TextField(blank=True)
	manuscript_summary = models.TextField(blank=True, help_text='Enrichment method summary for manuscripts')
	protocol_reference = models.TextField(blank=True)
	
class NuclearCaptureProtocol(Timestamped):
	name = models.CharField(max_length=150)
	start_date = models.DateField(null=True)
	end_date = models.DateField(null=True)
	description = models.TextField(blank=True)
	manuscript_summary = models.TextField(blank=True, help_text='Enrichment method summary for manuscripts')
	protocol_reference = models.TextField(blank=True)
	
class SequencingPlatform(Timestamped):
	platform = models.CharField(max_length=20)
	read_length = models.CharField(max_length=20, blank=True)
	note = models.TextField(blank=True)
	lanes_runs = models.FloatField(null=True, help_text='number of lanes for HISeqs or number of runs for Miseq and NextSeq')
	location = models.CharField(max_length=50, blank=True, help_text='location of sequencing platform')
	
class MTCapturePlate(Timestamped):
	name = models.CharField(max_length=30)
	protocol = models.ForeignKey(MTCaptureProtocol, on_delete=models.PROTECT, null=True)
	technician = models.CharField(max_length=10, blank=True)
	technician_fk = models.ForeignKey(WetLabStaff, on_delete=models.SET_NULL, null=True)
	date = models.DateField(null=True)
	robot = models.CharField(max_length=20, blank=True)
	notes = models.TextField(blank=True)
	
class MTSequencingRun(Timestamped):
	name = models.CharField(max_length=30)
	technician = models.CharField(max_length=10, blank=True)
	technician_fk = models.ForeignKey(WetLabStaff, on_delete=models.SET_NULL, null=True)
	date = models.DateField(null=True)
	sequencing = models.ForeignKey(SequencingPlatform, on_delete=models.SET_NULL, null=True)
	notes = models.TextField(blank=True)
	
class ShotgunPool(Timestamped):
	name = models.CharField(max_length=50)
	technician = models.CharField(max_length=10, blank=True)
	technician_fk = models.ForeignKey(WetLabStaff, on_delete=models.SET_NULL, null=True)
	date = models.DateField(null=True)
	notes = models.TextField(blank=True)
	
class ShotgunSequencingRun(Timestamped):
	name = models.CharField(max_length=50)
	technician = models.CharField(max_length=10, blank=True)
	technician_fk = models.ForeignKey(WetLabStaff, on_delete=models.SET_NULL, null=True)
	date = models.DateField(null=True)
	sequencing = models.ForeignKey(SequencingPlatform, on_delete=models.SET_NULL, null=True)
	notes = models.TextField(blank=True)
	
class NuclearCapturePlate(Timestamped):
	name = models.CharField(max_length=50)
	enrichment_type = models.CharField(max_length=20, blank=True)
	protocol = models.ForeignKey(NuclearCaptureProtocol, on_delete=models.PROTECT, null=True)
	technician = models.CharField(max_length=10, blank=True)
	technician_fk = models.ForeignKey(WetLabStaff, on_delete=models.SET_NULL, null=True)
	date = models.DateField(null=True)
	robot = models.CharField(max_length=50, blank=True)
	hyb_wash_temps = models.CharField(max_length=50, blank=True)
	notes = models.TextField(blank=True)
	
class NuclearSequencingRun(Timestamped):
	name = models.CharField(max_length=50)
	technician = models.CharField(max_length=10, blank=True)
	technician_fk = models.ForeignKey(WetLabStaff, on_delete=models.SET_NULL, null=True)
	date = models.DateField(null=True)
	sequencing = models.ForeignKey(SequencingPlatform, on_delete=models.SET_NULL, null=True)
	notes = models.TextField(blank=True)
	
class ControlsExtract(Timestamped):
	extract_batch = models.ForeignKey(ExtractBatch, on_delete=models.PROTECT)
	ec_count = models.PositiveSmallIntegerField(null=True)
	ec_median = models.FloatField(null=True)
	ec_max = models.FloatField(null=True)
	
class ControlsLibrary(Timestamped):
	library_batch = models.ForeignKey(LibraryBatch, on_delete=models.PROTECT)
	lc_count = models.PositiveSmallIntegerField(null=True)
	lc_median = models.FloatField(null=True)
	lc_max = models.FloatField(null=True)
	
class RadiocarbonShipment(Timestamped):
	ship_id = models.CharField(max_length=20, db_index=True, unique=True)
	ship_date = models.DateField(null=True)
	analysis_lab = models.CharField(max_length=50, blank=True)
	
class RadiocarbonCalibration(Timestamped):
	program = models.CharField(max_length=30, blank=True)
	version = models.CharField(max_length=30, blank=True)
	curve = models.CharField(max_length=30, blank=True)
	
class RadiocarbonDatingInvoice(Timestamped):
	invoice_number = models.CharField(max_length=20, db_index=True, unique=True)
	company_name = models.CharField(max_length=50, blank=True)
	billing_period = models.CharField(max_length=50, blank=True)
	billing_date = models.DateField(null=True)
	item_description = models.TextField(blank=True)
	number_of_samples = models.PositiveSmallIntegerField(null=True)
	total_charge = models.DecimalField(max_digits=9, decimal_places=2, null=True)
	note = models.TextField(blank=True)
	
class RadiocarbonDatedSample(Timestamped):
	sample = models.ForeignKey(Sample, on_delete=models.PROTECT)
	radiocarbon_shipment = models.ForeignKey(RadiocarbonShipment, on_delete=models.PROTECT, null=True)
	calibration = models.ForeignKey(RadiocarbonCalibration, on_delete=models.PROTECT, null=True)
	first_publication = models.ForeignKey(Publication, on_delete=models.PROTECT, null=True)
	notes = models.TextField(blank=True)
	material = models.CharField(max_length=50, blank=True)
	fraction_modern = models.FloatField(null=True)
	fraction_modern_plus_minus = models.FloatField(null=True)
	d14c_per_mille = models.FloatField(null=True)
	d14c_per_mille_plus_minus = models.FloatField(null=True)
	age_14c_bp = models.FloatField(null=True)
	age_14c_bp_plus_minus = models.FloatField(null=True)
	delta13c_per_mille = models.FloatField(null=True)
	delta15n_per_mille = models.FloatField(null=True)
	percent_carbon = models.FloatField(null=True)
	percent_nitrogen = models.FloatField(null=True)
	carbon_to_nitrogen_ratio = models.FloatField(null=True)
	run_date = models.DateField(null=True)
	lab_code = models.CharField(max_length=50, blank=True)
	oxcal_mu = models.FloatField(null=True)
	oxcal_sigma = models.FloatField(null=True)
	cal_from = models.IntegerField(null=True)
	cal_to = models.IntegerField(null=True)
	correction_applied = models.BooleanField(default=False)
	correction_note = models.TextField(blank=True)
	payment_lab = models.CharField(max_length=50, blank=True)
	invoice = models.ForeignKey(RadiocarbonDatingInvoice, on_delete=models.PROTECT, null=True)
	
class DistributionsShipment(Timestamped):
	collaborator = models.ForeignKey(Collaborator, on_delete=models.PROTECT)
	date = models.DateField(null=True, help_text='Distribution shipment date')
	shipment_method = models.CharField(max_length=20, blank=True, help_text='Shipment method used to send samples: FedEx, USPS, hand carried')
	shipment_tracking_number = models.CharField(max_length=30, blank=True, help_text='Courier package tracking number')
	shipment_notes = models.TextField(help_text='Any notes associated with the distribution shipment', blank=True)
	delivery_date = models.DateField(help_text='Date distribution shipment was delivered', null=True)
	delivery_notes = models.TextField(help_text='Any notes assoicated with the distribution delivery: person confirming delivery, etc.', blank=True)
	
class DistributionsPowder(Timestamped):
	distribution_shipment = models.ForeignKey(DistributionsShipment, on_delete=models.PROTECT)
	powder_sample = models.ForeignKey(PowderSample, on_delete=models.PROTECT)
	powder_sent_mg = models.FloatField(help_text='Total milligrams of bone powder distributed')
	
class DistributionsLysate(Timestamped):
	distribution_shipment = models.ForeignKey(DistributionsShipment, on_delete=models.PROTECT)
	lysate = models.ForeignKey(Lysate, on_delete=models.PROTECT)
	lysate_sent_ul = models.FloatField(help_text='Total microliters of lysate distributed')
	
class DistributionsExtract(Timestamped):
	distribution_shipment = models.ForeignKey(DistributionsShipment, on_delete=models.PROTECT)
	extract = models.ForeignKey(Extract, on_delete=models.PROTECT)
	extract_sent_ul = models.FloatField(help_text='Total microliters of extract distributed')
	
class Results(Timestamped):
	library_id = models.CharField(max_length=25, db_index=True)
	library_fk = models.ForeignKey(Library, null=True, on_delete=models.SET_NULL)
	mt_capture_plate = models.ForeignKey(MTCapturePlate, null=True, on_delete=models.SET_NULL)
	mt_seq_run = models.ForeignKey(MTSequencingRun, null=True, on_delete=models.SET_NULL)
	shotgun_pool = models.ForeignKey(ShotgunPool, null=True, on_delete=models.SET_NULL)
	shotgun_seq_run = models.ForeignKey(ShotgunSequencingRun, null=True, on_delete=models.SET_NULL)
	nuclear_capture_plate = models.ForeignKey(NuclearCapturePlate, null=True, on_delete=models.SET_NULL)
	nuclear_seq_run = models.ForeignKey(NuclearSequencingRun, null=True, on_delete=models.SET_NULL)
	extract_control = models.ForeignKey(ControlsExtract, null=True, on_delete=models.SET_NULL)
	library_control = models.ForeignKey(ControlsLibrary, null=True, on_delete=models.SET_NULL)

# enumeration of assessment categories
class AssessmentCategory(models.Model):
	category = models.CharField(max_length=25, unique=True)
	description = models.TextField(blank=True)
	sort_order = models.SmallIntegerField()

# David Reich's anno file is a series of instances
class Instance(Timestamped):
	instance_id = models.CharField(max_length=40, db_index=True)
	master_id = models.CharField(max_length=40, db_index=True)
	reich_lab_id = models.PositiveIntegerField(db_index=True, null=True, help_text='Lowest Reich Lab sample ID for this individual')
	
	library_ids = models.ManyToManyField(Library) # this is implicitly a list of samples as well
	published_year = models.PositiveSmallIntegerField(null=True)
	publication = models.CharField(max_length=50, blank=True)
	group_id = models.CharField(max_length=120)
	
	data_type = models.CharField(max_length=20) # TODO enumerate this 1240k, shotgun, BigYoruba, etc.
	family = models.TextField(blank=True, help_text='family id and position within family')
	assessment_notes = models.TextField(help_text='Xcontam listed if |Z|>2 standard errors from zero: 0.02-0.05="QUESTIONABLE", >0.05="QUESTIONABLE_CRITICAL" or "FAIL") (mtcontam 97.5th percentile estimates listed if coverage >2: <0.8 is "QUESTIONABLE_CRITICAL", 0.8-0.95 is "QUESTIONABLE", and 0.95-0.98 is recorded but "PASS", gets overriden by ANGSD')
