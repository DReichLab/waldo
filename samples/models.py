from django.db import models
from django.utils import timezone
from datetime import date

from django.contrib.auth.models import User

from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.utils.translation import gettext_lazy as _

from django.db.models import Max, Min

from .layout import PLATE_ROWS, PLATE_WELL_COUNT, PLATE_WELL_COUNT_HALF, validate_row_letter, plate_location, reverse_plate_location_coordinate, reverse_plate_location, duplicate_positions_check_db, p7_qbarcode_source, barcodes_for_location

import re, string

REICH_LAB = 'Reich Lab'

def parse_sample_string(s):
	# we expect a sample number to start with 'S'
	# S1234a
	match = re.fullmatch('S([\d]+)([a-z]{0,2})', s)
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

single_controls = []
a_controls = []
b_controls = []
c_controls = []
for c in string.ascii_lowercase:
	single_controls += [c]
	a_controls += [f'a{c}']
	b_controls += [f'b{c}']
	c_controls += [f'c{c}']
CONTROL_CHARACTERS = single_controls + a_controls + b_controls + c_controls

class Sample(Timestamped):
	reich_lab_id = models.PositiveIntegerField(db_index=True, null=True, help_text=' assigned when a sample is selected from the queue by the wetlab')
	control = models.CharField(max_length=2, blank=True, help_text='Non-empty value indicates this is a control')
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
	powder_batch = models.ForeignKey(PowderBatch, on_delete=models.CASCADE, help_text='powder belongs to this processing batch', null=True)
	storage = models.ForeignKey(Storage, on_delete=models.PROTECT, null=True)
	
	sampling_tech = models.CharField(max_length=15, blank=True, help_text='Technique used to produce the bone powder')
	sampling_notes = models.TextField(help_text='Notes from technician about sample quality, method used, mg of bone powder produced and storage location', blank=True)
	total_powder_produced_mg = models.FloatField(null=True, help_text='Total milligrams of bone powder produced from the sample')
	powder_for_extract = models.FloatField(default=0, help_text='Milligrams of powder used for extract') # This is stored here temporarily as it is more properly a property of the extract.
	storage_location = models.CharField(max_length=50, blank=True, help_text='Storage location of remaining bone powder')
	sample_prep_lab = models.CharField(max_length=50, blank=True, help_text='Name of lab where bone powder was produced')
	sample_prep_protocol = models.ForeignKey(SamplePrepProtocol, on_delete=models.SET_NULL, null=True)
	
	def is_control(self):
		return self.powder_sample_id.endswith('NP')
		
	@staticmethod
	def spreadsheet_header():
		return ['powder_sample_id',
			'sampling_notes',
			'total_powder_produced_mg',
			'powder_for_extract',
			'storage_location',
			'sample_prep_lab',
			'sample_prep_protocol']
		
	# for wetlab spreadsheet, return array to output as tsv
	# order corresponds to the spreadsheet header
	def to_spreadsheet_row(self):
		return [self.powder_sample_id,
			self.sampling_notes,
			self.total_powder_produced_mg,
			self.powder_for_extract,
			self.storage_location,
			self.sample_prep_lab,
			self.sample_prep_protocol.preparation_method
		]
	# from wetlab spreadsheet
	def from_spreadsheet_row(self, headers, arg_array, user):
		self.sampling_notes = arg_array[headers.index('sampling_notes')]
		self.total_powder_produced_mg = float( arg_array[headers.index('total_powder_produced_mg')])
		self.powder_for_extract = float(arg_array[headers.index('powder_for_extract')])
		self.storage_location = arg_array[headers.index('storage_location')]
		self.sample_prep_lab = arg_array[headers.index('sample_prep_lab')]
		self.sample_prep_protocol = SamplePrepProtocol.objects.get(preparation_method=arg_array[headers.index('sample_prep_protocol')])
		self.save(save_user=user)
	
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
	active = models.BooleanField(default=True)
	
	def lysate_volume_used(self):
		return self.total_lysis_volume * self.lysate_fraction_extracted
	
# enumeration of the control types
class ControlType(models.Model):
	control_type = models.CharField(max_length=25, unique=True)
	
# the set of controls for a plate. Each control has a ControlLayout element containing its plate position.
class ControlSet(Timestamped):
	layout_name = models.CharField(max_length=25, db_index=True, unique=True)
	notes = models.TextField(blank=True)
	active = models.BooleanField(default=True)

# each control layout comprises rows with the same name
# a control layout is applied to batch layouts to add controls
class ControlLayout(TimestampedWellPosition):
	control_set = models.ForeignKey(ControlSet, on_delete=models.CASCADE, null=True)
	control_type = models.ForeignKey(ControlType, on_delete=models.PROTECT)
	active = models.BooleanField(default=True)

EXTRACT_NEGATIVE = 'Extract Negative'
LIBRARY_NEGATIVE = 'Library Negative'
LIBRARY_POSITIVE = 'Library Positive'

EXTRACT_AND_LIBRARY_CONTROLS = [EXTRACT_NEGATIVE, LIBRARY_NEGATIVE, LIBRARY_POSITIVE]

# extract negative and library negative controls get Reich lab sample numbers
# find the sample number for one of these types from extract batch layout elements
def control_sample_number(control_element_queryset):
	reich_lab_sample_number = None
	for control_layout_element in control_element_queryset:
		if reich_lab_sample_number is None:
			reich_lab_sample_number = control_layout_element.powder_sample.sample.reich_lab_id
		elif reich_lab_sample_number != control_layout_element.powder_sample.sample.reich_lab_id:
			raise ValueError(f'Multiple control sample ids: {reich_lab_sample_number} {control_layout_element.powder_sample.sample.reich_lab_id:}')
	return reich_lab_sample_number
	
# How many lysates are there for this sample
def lysates_for_sample(sample):
	existing_lysates = Lysate.objects.filter(powder_sample__sample=sample)
	return len(existing_lysates)

# this creates a lysate for a layout_element if it does not exist, and returns the existing one otherwise
def create_lysate(lysate_layout_element, lysate_batch, user):
	powder_sample = lysate_layout_element.powder_sample
	# library positive controls do not have powder sample
	if powder_sample is None:
		return None
	# only create the lysate from powder for this well once
	elif lysate_layout_element.lysate is not None:
		return lysate_layout_element.lysate
	else:
		sample = powder_sample.sample
		next_lysate_number = lysates_for_sample(sample) +1
		lysate_id = f'{str(sample)}.Y{next_lysate_number}'
		print(f'created lysate id {lysate_id}')
		lysate = Lysate(lysate_id=lysate_id,
					reich_lab_lysate_number=next_lysate_number,
					powder_sample=powder_sample,
					lysate_batch=lysate_batch,
					powder_used_mg=powder_sample.powder_for_extract,
					total_volume_produced=lysate_batch.protocol.total_lysis_volume)
		lysate.save(save_user=user)
		lysate_layout_element.lysate = lysate
		lysate_layout_element.save(save_user=user)
		
		return lysate

# turn powders into lysates
class LysateBatch(Timestamped):
	batch_name = models.CharField(max_length=50, unique=True)
	protocol = models.ForeignKey(ExtractionProtocol, on_delete=models.PROTECT, null=True)
	technician = models.CharField(max_length=50, blank=True)
	technician_fk = models.ForeignKey(WetLabStaff, on_delete=models.SET_NULL, null=True)
	date = models.DateField(null=True, help_text='YYYY-MM-DD')
	robot = models.CharField(max_length=20, blank=True)
	note = models.TextField(blank=True)
	layout = models.ManyToManyField(PowderSample, through='LysateBatchLayout', related_name='powder_sample_assignment')
	control_set = models.ForeignKey(ControlSet, on_delete=models.SET_NULL, null=True)
	
	OPEN = 0
	LYSATES_CREATED = 1
	LYSATE_BATCH_STATES = (
		(OPEN, 'Open'),
		(LYSATES_CREATED, 'Lysates created')
	)
	status = models.PositiveSmallIntegerField(default = OPEN, choices=LYSATE_BATCH_STATES)
	
	# return string representing status. For templates
	def get_status(self):
		return self.LYSATE_BATCH_STATES[self.status][1]
		
	# retain only powder samples in layout_element_ids
	# in addition, preserve controls
	def restrict_layout_elements(self, layout_element_ids):
		to_clear = LysateBatchLayout.objects.filter(lysate_batch=self).exclude(id__in=layout_element_ids).exclude(control_type__isnull=False)
		to_clear.delete()
	
	# add LysateBatchLayout for powder samples
	# this always adds a new layout element
	def assign_powder_samples(self, new_powder_sample_ids, user):
		DEFAULT_ROW = 'A'
		DEFAULT_COLUMN = 1
		for powder_sample_id in new_powder_sample_ids:
			powder_sample = PowderSample.objects.get(id=powder_sample_id)
			powder_sample_mass_for_extract = powder_sample.powder_for_extract
			
			lysate_batch_layout = LysateBatchLayout(lysate_batch=self,
									powder_sample=powder_sample,
									row=DEFAULT_ROW,
									column=DEFAULT_COLUMN,
									powder_used_mg = powder_sample_mass_for_extract,
									)
			lysate_batch_layout.save(save_user = user)
			
	def num_controls(self):
		existing_controls = LysateBatchLayout.objects.filter(lysate_batch=self, control_type__isnull=False)
		return existing_controls.count()
	
	# assign a layout, one powder sample or control per position
	# this is the layout to produce lysate
	def assign_layout(self, user):
		control_types = EXTRACT_AND_LIBRARY_CONTROLS
		# sort powder batches by lowest sample ID, then powder batch by reich lab id
		# powder batches are grouped together, and sample numbers are ascending
		powders = LysateBatchLayout.objects.annotate(powder_batch_order=Min('powder_sample__powder_batch__powdersample__sample__reich_lab_id')).filter(lysate_batch=self, control_type=None).order_by('powder_batch_order', 'powder_sample__powder_batch', 'powder_sample__sample__reich_lab_id')
		controls = ControlLayout.objects.filter(control_set=self.control_set, control_type__control_type__in=control_types, active=True).order_by('column', 'row')
		# check count
		if powders.count() + controls.count() > PLATE_WELL_COUNT:
			raise ValueError(f'Too many items for extract layout: {powders.count} powders and {controls.count} controls')
		
		# get existing controls
		existing_controls = LysateBatchLayout.objects.filter(lysate_batch=self, control_type__isnull=False).order_by('column', 'row')
		# we check the existing controls for sample ids
		# Extract Negative: find the Reich lab sample ID used for extract negatives for this extract batch
		extract_negative_controls = existing_controls.filter(control_type__control_type=EXTRACT_NEGATIVE)
		extract_negative_sample_id = control_sample_number(extract_negative_controls)
		# Library Negative: find the Reich lab sample ID used for library negatives for this extract batch
		library_negative_controls = existing_controls.filter(control_type__control_type=LIBRARY_NEGATIVE)
		library_negative_sample_id = control_sample_number(library_negative_controls)
		
		# remove existing control layout entries
		for existing_control in existing_controls:
			existing_control.destroy_control(user)
			existing_control.delete()
		# create new control layout entries
		extract_negative_control_count = 0
		library_negative_control_count = 0
		for control in controls:
			layout_element = LysateBatchLayout(lysate_batch=self, control_type=control.control_type, row=control.row, column=control.column, powder_used_mg=0)
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

		completed_controls = LysateBatchLayout.objects.filter(lysate_batch=self, control_type__isnull=False).order_by('column', 'row')
		count = 0
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
				for control in completed_controls:
					if control.same_position(layout_element):
						control_free_position = False
						break
				# if there is no control in this position, we are done with this powder
				if control_free_position:
					break
			layout_element.save(save_user=user)
	
	# Empty wells become library negatives
	def fill_empty_wells_with_library_negatives(self, user):
		# order consistent with plate_location
		existing_layout = LysateBatchLayout.objects.filter(lysate_batch=self).order_by('column', 'row')
		library_negatives = existing_layout.filter(control_type__control_type=LIBRARY_NEGATIVE)
		num_library_negatives = len(library_negatives)
		control_type = library_negatives[0].control_type
		library_negative_sample_id = library_negatives[0].powder_sample.sample.reich_lab_id
		
		# well positions are in [0,95], fill these one per loop pass
		layout_iterator = existing_layout.iterator()
		current_existing = -1
		has_remaining_elements = True
		for next_to_fill in range(PLATE_WELL_COUNT):
			while current_existing < next_to_fill and has_remaining_elements:
				try:
					layout_element = next(layout_iterator)
					current_existing = reverse_plate_location_coordinate(layout_element.row, layout_element.column)
				except StopIteration:
					has_remaining_elements = False
			# this well position is occupied, so proceed to next position
			if current_existing == next_to_fill:
				pass
			else: # this well position is unoccupied, so fill with new library negative
				row, column = plate_location(next_to_fill)
				control_character = CONTROL_CHARACTERS[num_library_negatives]
				num_library_negatives += 1
				control_sample = Sample(reich_lab_id=library_negative_sample_id, control=control_character)
				control_sample.save(save_user=user)
				powder_sample_control = PowderSample(sample=control_sample, powder_sample_id=f'{str(control_sample)}.NP')
				powder_sample_control.save(save_user=user)
				layout_element = LysateBatchLayout(lysate_batch=self, control_type=control_type, row=row, column=column, powder_used_mg=0, powder_sample=powder_sample_control)
				layout_element.save(save_user=user)
				
	def create_lysates(self, user):
		layout = LysateBatchLayout.objects.filter(lysate_batch=self)
		duplicate_positions_check_db(layout)
		for layout_element in layout:
			# create lysate entry, if it does not exist
			lysate = create_lysate(layout_element, self, user)
	
	def create_extract_batch(self, batch_name, user):
		layout = LysateBatchLayout.objects.filter(lysate_batch=self)
		duplicate_positions_check_db(layout)
		try:
			extract_batch = ExtractionBatch.objects.get(batch_name=batch_name)
			raise ValueError(f'ExtractionBatch {batch_name} already exists')
		except ExtractionBatch.DoesNotExist:
			wetlab_staff = WetLabStaff.objects.get(login_user=user)
			extract_batch = ExtractionBatch(batch_name=batch_name,
								protocol = self.protocol,
								technician = wetlab_staff.initials(),
								technician_fk = wetlab_staff,
								control_set = self.control_set)
			extract_batch.save(save_user=user)
			for layout_element in layout:
				lysate = layout_element.lysate
				# create corresponding extract batch layout
				extract_batch_layout_element = ExtractionBatchLayout(extract_batch=extract_batch,
									lysate = lysate,
									control_type = layout_element.control_type,
									lysate_volume_used = (self.protocol.total_lysis_volume * self.protocol.lysate_fraction_extracted),
									row = layout_element.row,
									column = layout_element.column
									)
				extract_batch_layout_element.save(save_user=user)
			
		return extract_batch
		
	def lysates_from_spreadsheet(self, spreadsheet, user):
		s = spreadsheet.read().decode("utf-8")
		lysates = Lysate.objects.filter(lysate_batch=self)
		lines = s.split('\n')
		header = lines[0].strip()
		headers = re.split('\t|\n', header)
		if headers[0] != 'lysate_id':
			raise ValueError('lysate_id is not first')
			
		for line in lines[1:]:
			fields = re.split('\t|\n', line)
			lysate_id = fields[0]
			if len(lysate_id) > 0:
				lysate = lysates.get(lysate_id=lysate_id)
				lysate.from_spreadsheet_row(headers, fields, user)

class Lysate(Timestamped):
	lysate_id = models.CharField(max_length=15, unique=True, null=False, db_index=True)
	reich_lab_lysate_number = models.PositiveIntegerField(null=True, help_text='Starts at 1 for each sample.')
	powder_sample = models.ForeignKey(PowderSample, null=True, on_delete=models.PROTECT)
	lysate_batch = models.ForeignKey(LysateBatch, null=True, on_delete=models.CASCADE)
	storage = models.ForeignKey(Storage, on_delete=models.PROTECT, null=True)
	
	powder_used_mg = models.FloatField(null=True, help_text='milligrams of bone powder used in lysis')
	total_volume_produced = models.FloatField(null=True, help_text='Total microliters of lysate produced')
	
	plate_id = models.CharField(max_length=12, blank=True, help_text='FluidX rack barcode')
	position = models.CharField(max_length=3, blank=True, help_text='well/tube position in plate/rack')
	barcode = models.CharField(max_length=12, blank=True, help_text='Physical barcode on FluidX tube')
	notes = models.TextField(blank=True)
	
	@staticmethod
	def spreadsheet_header():
		return ['lysate_id',
			'powder_used_mg',
			'total_volume_produced',
			'plate_id',
			'position',
			'barcode',
			'notes']
		
	def to_spreadsheet_row(self):
		field_list = Lysate.spreadsheet_header()
		values = []
		for field in field_list:
			values.append(getattr(self, field))
		return values
		
	def from_spreadsheet_row(self, headers, arg_array, user):
		row_lysate_id = arg_array[headers.index('lysate_id')]
		if self.lysate_id != row_lysate_id:
			raise ValueError(f'lysate_id mismatch {self.lysate_id} {row_lysate_id}')
		self.powder_used_mg = float(arg_array[headers.index('powder_used_mg')])
		self.total_volume_produced = float(arg_array[headers.index('total_volume_produced')])
		self.position = arg_array[headers.index('position')]
		self.barcode = arg_array[headers.index('barcode')]
		self.notes = arg_array[headers.index('notes')]
		self.save(save_user=user)
		
	# Compute how much lysate is left based on original lysate amount generated minus:
	# 1. lysate used to make extracts
	# 2. lost lysate
	def remaining(self):
		lysate_used = 0
		# Rebecca kept track of lysate used in extracts
		# potential improvement is to move all of these computations into ExtractionBatchLayout objects
		extracts = Extract.objects.filter(lysate=self)
		for extract in extracts:
			lysate_used += extract.lysis_volume_extracted
		# Lost lysate is in ExtractionBatchLayout
		lost_lysates = ExtractionBatchLayout.objects.filter(lysate=self, extract_batch=None)
		for lost in lost_lysates:
			lysate_used += lost.lysate_volume_used
		lysate_remaining = self.total_volume_produced - lysate_used
		return lysate_remaining
	
# how many extracts exist for this lysate
def extracts_for_lysate(lysate):
	existing_extracts = Extract.objects.filter(lysate=lysate)
	return len(existing_extracts)
	
# powder -> lysate
class LysateBatchLayout(TimestampedWellPosition):
	lysate_batch = models.ForeignKey(LysateBatch, on_delete=models.CASCADE, null=True) # use a null lysate batch to mark lost powder
	powder_sample = models.ForeignKey(PowderSample, on_delete=models.CASCADE, null=True)
	control_type = models.ForeignKey(ControlType, on_delete=models.PROTECT, null=True)
	powder_used_mg = models.FloatField()
	notes = models.TextField(blank=True)
	lysate = models.ForeignKey(Lysate, on_delete=models.SET_NULL, null=True, help_text='Lysate created in this well from powder')
	
	def destroy_control(self, user):
		if self.control_type is not None:
			if self.powder_sample is not None:
				to_delete_powder_sample = self.powder_sample
				self.powder_sample = None
				to_delete_sample = to_delete_powder_sample.sample
				if not to_delete_powder_sample.is_control():
					raise ValueError(f'{to_delete_powder_sample.powder_sample_id} does not appear to be a control')
				if not to_delete_sample.is_control():
					raise ValueError(f'{to_delete_sample.reich_lab_id} does not appear to be a control')
				to_delete_powder_sample.delete()
				to_delete_sample.delete()
				self.save(save_user=user)
				
	def clean(self):
		super(LysateBatchLayout, self).clean()
		if self.powder_sample is None and (self.lysate_batch is None or self.control_type is None):
			print('Null powder samples must be extract batch controls')
			raise ValidationError(_('Null powder samples must be extract batch controls'))
	
def create_extract_from_lysate(extract_layout_element, user):
	lysate = extract_layout_element.lysate
	
	if lysate is None:
		return None
	elif extract_layout_element.extract is not None:
		return extract_layout_element.extract
	else:
		extract_batch = extract_layout_element.extract_batch
		lysis_volume_extracted = extract_batch.protocol.total_lysis_volume * extract_batch.protocol.lysate_fraction_extracted
		
		sample = lysate.powder_sample.sample
		next_extract_number = extracts_for_lysate(lysate) +1
		extract_id = f'{str(lysate.lysate_id)}.E{next_extract_number}'
		print(f'created extract id {extract_id}')
		extract = Extract(extract_id=extract_id,
					reich_lab_extract_number=next_extract_number,
					lysate=lysate,
					sample=sample,
					extract_batch=extract_batch,
					lysis_volume_extracted=lysis_volume_extracted,
					extraction_lab=REICH_LAB)
		extract.save(save_user=user)
		
		extract_layout_element.extract = extract
		extract_layout_element.lysate_volume_used = lysis_volume_extracted
		extract_layout_element.save(save_user=user)
		return extract
	
class ExtractionBatch(Timestamped):
	batch_name = models.CharField(max_length=50, unique=True)
	protocol = models.ForeignKey(ExtractionProtocol, on_delete=models.PROTECT, null=True)
	technician = models.CharField(max_length=50, blank=True)
	technician_fk = models.ForeignKey(WetLabStaff, on_delete=models.SET_NULL, null=True)
	date = models.DateField(null=True, help_text='YYYY-MM-DD')
	robot = models.CharField(max_length=20, blank=True)
	note = models.TextField(blank=True)
	layout = models.ManyToManyField(Lysate, through='ExtractionBatchLayout', related_name='lysate_assignment')
	control_set = models.ForeignKey(ControlSet, on_delete=models.SET_NULL, null=True)
	
	OPEN = 0
	EXTRACTED = 1
	EXTRACT_BATCH_STATES = (
		(OPEN, 'Open'),
		(EXTRACTED, 'Extracted')
	)
	status = models.PositiveSmallIntegerField(default = OPEN, choices=EXTRACT_BATCH_STATES)
	
	# return string representing status. For templates
	def get_status(self):
		return self.EXTRACT_BATCH_STATES[self.status][1]
	
	# retain only lysates in layout_element_ids
	# in addition, preserve controls
	def restrict_layout_elements(self, layout_element_ids):
		to_clear = ExtractionBatchLayout.objects.filter(extract_batch=self).exclude(id__in=layout_element_ids).exclude(control_type__isnull=False)
		to_clear.delete()
		
	def create_extracts(self, user):
		layout = ExtractionBatchLayout.objects.filter(extract_batch=self)
		duplicate_positions_check_db(layout)
		# create extracts
		for layout_element in layout:
			extract = create_extract_from_lysate(layout_element, user)
	
	def create_library_batch(self, batch_name, user):
		layout = ExtractionBatchLayout.objects.filter(extract_batch=self)
		duplicate_positions_check_db(layout)
		try:
			library_batch = LibraryBatch.objects.get(name=batch_name)
			raise ValueError(f'LibraryBatch {batch_name} already exists')
		except LibraryBatch.DoesNotExist:
			wetlab_staff = WetLabStaff.objects.get(login_user=user)
			library_batch = LibraryBatch(name=batch_name,
								technician = wetlab_staff.initials(),
								technician_fk = wetlab_staff,
								)
			library_batch.save(save_user=user)
			
			# layout for library batch with same layout
			for layout_element in layout:
				# create corresponding library batch layout element
				library_batch_layout_element = LibraryBatchLayout(library_batch=library_batch,
									extract=layout_element.extract,
									control_type = layout_element.control_type,
									row = layout_element.row,
									column = layout_element.column
					)
				library_batch_layout_element.save(save_user=user)
	
	def extracts_from_spreadsheet(self, spreadsheet, user):
		s = spreadsheet.read().decode("utf-8")
		extracts = Extract.objects.filter(extract_batch=self)
		lines = s.split('\n')
		header = lines[0].strip()
		headers = re.split('\t|\n', header)
		if headers[0] != 'extract_id':
			raise ValueError('extract_id is not first')
			
		for line in lines[1:]:
			fields = re.split('\t|\n', line)
			extract_id = fields[0]
			if len(extract_id) > 0:
				extract = extracts.get(extract_id=extract_id)
				extract.from_spreadsheet_row(headers, fields, user)
	
class Extract(Timestamped):
	extract_id = models.CharField(max_length=20, unique=True, db_index=True)
	reich_lab_extract_number = models.PositiveIntegerField(null=True, help_text='Starts at 1 for each lysate or sample if no lysate exists.')
	lysate = models.ForeignKey(Lysate, on_delete=models.PROTECT, null=True)
	sample = models.ForeignKey(Sample, on_delete=models.PROTECT, null=True)
	lysate_batch = models.ForeignKey(LysateBatch, null=True, on_delete=models.PROTECT)
	extract_batch = models.ForeignKey(ExtractionBatch, null=True, on_delete=models.CASCADE)
	storage = models.ForeignKey(Storage, on_delete=models.PROTECT, null=True)
	lysis_volume_extracted = models.FloatField(null=True)
	#extract_volume_remaining = models.FloatField(null=True)
	notes = models.TextField(blank=True)
	storage_location = models.TextField(blank=True)
	extraction_lab = models.CharField(max_length=50, blank=True, help_text='Name of lab where DNA extraction was done')
	
	@staticmethod
	def spreadsheet_header():
		return ['extract_id',
			'lysis_volume_extracted',
			'notes',
			#'storage_location',
			]
		
	def to_spreadsheet_row(self):
		field_list = Extract.spreadsheet_header()
		values = []
		for field in field_list:
			values.append(getattr(self, field))
		return values
		
	def from_spreadsheet_row(self, headers, arg_array, user):
		row_extract_id = arg_array[headers.index('extract_id')]
		if self.extract_id != row_extract_id:
			raise ValueError(f'extract_id mismatch {self.extract_id} {row_extract_id}')
		self.lysis_volume_extracted = float(arg_array[headers.index('lysis_volume_extracted')])
		self.notes = arg_array[headers.index('notes')]
		self.storage_location = arg_array[headers.index('storage_location')]
		self.save(save_user=user)
	
# lysate -> extract
class ExtractionBatchLayout(TimestampedWellPosition):
	extract_batch = models.ForeignKey(ExtractionBatch, on_delete=models.CASCADE, null=True) # use a null extract batch to mark lost lysate
	lysate = models.ForeignKey(Lysate, on_delete=models.CASCADE, null=True)
	control_type = models.ForeignKey(ControlType, on_delete=models.PROTECT, null=True)
	lysate_volume_used = models.FloatField()
	notes = models.TextField(blank=True)
	extract = models.ForeignKey(Extract, on_delete=models.SET_NULL, null=True, help_text='extract created in this well location')
	
class LibraryProtocol(Timestamped):
	name = models.CharField(max_length=50, unique=True)
	start_date = models.DateField(null=True)
	end_date = models.DateField(null=True)
	description = models.TextField(blank=True)
	manuscript_summary = models.CharField(max_length=50, blank=True)
	protocol_reference = models.TextField(blank=True)
	manual_robotic = models.CharField(max_length=20, blank=True)
	volume_extract_used_standard = models.FloatField(null=True)
	
	udg_treatment = models.CharField(max_length=10, null=True)
	library_type = models.CharField(max_length=2, null=True)
	
def libraries_for_extract(extract):
	libraries = Library.objects.filter(extract=extract)
	return len(libraries)

# Create the library corresponding
def create_library_from_extract(layout_element, user):
	library_batch = layout_element.library_batch
	extract = layout_element.extract
	
	if extract is None:
		return None
	elif layout_element.library is not None:
		return layout_element.library
	else:
		existing_libraries = libraries_for_extract(extract)
		next_library_number = existing_libraries + 1
		# TODO check existing extract amount
		# assign barcodes
		if library_batch.protocol.library_type == 'ds':
			int_position = reverse_plate_location_coordinate(layout_element.row, layout_element.column)
			p5_qstr, p7_qstr = barcodes_for_location(int_position, library_batch.p7_offset)
			p5_barcode = Barcode.objects.get(label = p5_qstr)
			p7_barcode = Barcode.objects.get(label = p7_qstr)
		elif library_batch.protocol.library_type == 'ss':
			raise ValueError(f'single stranded TODO')
		else:
			raise ValueError(f'unhandled library type {library_batch.protocol.library_type}')
		library = Library(sample = extract.sample,
						extract = extract,
						library_batch = library_batch,
						reich_lab_library_id = f'{extract.extract_id}.L{next_library_number}',
						reich_lab_library_number = next_library_number,
						udg_treatment = library_batch.protocol.udg_treatment,
						library_type = library_batch.protocol.library_type,
						library_prep_lab = REICH_LAB,
						ul_extract_used = library_batch.protocol.volume_extract_used_standard,
						p5_barcode = p5_barcode,
						p7_barcode = p7_barcode
					)
		library.save(save_user=user)
		layout_element.library = library
		layout_element.ul_extract_used = library.ul_extract_used
		layout_element.save(save_user=user)
		return library
	
def validate_even(value):
	if value % 2 != 0:
		raise ValidationError(
			_('%(value)s is not an even number'),
			params={'value': value},
		)

class LibraryBatch(Timestamped):
	name = models.CharField(max_length=150, blank=True)
	protocol = models.ForeignKey(LibraryProtocol, on_delete=models.PROTECT, null=True)
	technician = models.CharField(max_length=50, blank=True)
	prep_date = models.DateField(null=True, help_text='YYYY-MM-DD')
	prep_note = models.TextField(blank=True)
	prep_robot = models.CharField(max_length=20, blank=True)
	cleanup_robot = models.CharField(max_length=20, blank=True)
	qpcr_machine = models.CharField(max_length=20, blank=True)
	technician_fk = models.ForeignKey(WetLabStaff, on_delete=models.SET_NULL, null=True)
	
	# The offset determines completely the layout of barcodes for the library batch because the wetlab uses a system where the p5 barcodes are placed in the same location for all plates
	# If we need to handle arbitrary layouts, migrate this state into barcodes in the layout objects 
	p7_offset = models.SmallIntegerField(null=True, validators=[MinValueValidator(0), MaxValueValidator(PLATE_WELL_COUNT_HALF-1), validate_even], help_text='Must be even in [0,46]')
	
	OPEN = 0
	LIBRARIED = 1
	LIBRARY_BATCH_STATES = (
		(OPEN, 'Open'),
		(LIBRARIED, 'Libraried')
	)
	status = models.PositiveSmallIntegerField(default = OPEN, choices=LIBRARY_BATCH_STATES)
	
	def check_p7_offset(self):
		if self.p7_offset is None or self.p7_offset < 0 or self.p7_offset >= PLATE_WELL_COUNT_HALF:
			raise ValueError(f'p7_offset is out of range: {self.p7_offset}')
	
	def create_libraries(self, user):
		self.check_p7_offset()
		layout = LibraryBatchLayout.objects.filter(library_batch=self)
		duplicate_positions_check_db(layout)
		
		for layout_element in layout:
			create_library_from_extract(layout_element, user)
			
	def get_robot_layout(self):
		self.check_p7_offset()
		entries = []
		for position in range(PLATE_WELL_COUNT):
			row, column = plate_location(position) # for example, A1
			destination = f'{row}{column}'
			p5, p7 = barcodes_for_location(position, self.p7_offset) # robot needs p7. p5 is already known for each location. 
			source = p7_qbarcode_source(p7)
			entries.append([source, destination, 1]) # TODO fix elements
		return entries
			
	# extract_ids are numeric primary key
	# currently this unassigns only
	def assign_extracts_to_library_batch(self, extract_ids, user):
		# remove extracts that are assigned but preserve controls
		to_clear = LibraryBatchLayout.objects.filter(library_batch=self).exclude(extract_id__in=extract_ids).exclude(control_type__isnull=False)
		to_clear.delete()
		
	def extracts_from_spreadsheet(self, spreadsheet, user):
		s = spreadsheet.read().decode("utf-8")
		libraries = Library.objects.filter(library_batch=self)
		lines = s.split('\n')
		header = lines[0].strip()
		headers = re.split('\t|\n', header)
		if headers[0] != 'well_position':
			raise ValueError('well_position is not first')
		if headers[0] != 'reich_lab_library_id':
			raise ValueError('reich_lab_library_id is not second')
			
		for line in lines[1:]:
			fields = re.split('\t|\n', line)
			reich_lab_library_id = fields[1]
			if len(reich_lab_library_id) > 0:
				library = libraries.get(reich_lab_library_id=reich_lab_library_id)
				library.from_spreadsheet_row(headers, fields, user)
		
	def create_capture(self, user):
		# TODO control changes for capture
		# 1. Move library negative in H12 to H9
		# 2. Replace library positive with PCR negative (G12)
		# 3. capture positive in H12
		pass
	
def validate_index_dna_sequence(sequence):
	valid_bases = 'ACGT'
	for base in sequence:
		if base not in valid_bases:
			raise ValidationError(
				_('%(base)s is not a valid DNA base'),
				params={'base': base},
			)
		
def validate_barcode_dna_sequence(sequence):
	barcodes = sequence.split(':')
	for barcode in barcodes:
		if len(barcode) > 0:
			validate_index_dna_sequence(sequence)
		else:
			raise ValidationError(_('%(sequence)s contains empty barcode'), params={'sequence': sequence})
	
class Barcode(models.Model):
	label = models.CharField(max_length=10, db_index=True)
	sequence = models.CharField(max_length=31, db_index=True, unique=True, validators=[validate_barcode_dna_sequence])
	
class P5_Index(models.Model):
	label = models.CharField(max_length=10, db_index=True) # cannot be unique because double and single stranded are named with same integers
	label2 = models.CharField(max_length=20, blank=True)
	sequence = models.CharField(max_length=8, db_index=True, unique=True, validators=[validate_index_dna_sequence])
	
class P7_Index(models.Model):
	label = models.CharField(max_length=10, db_index=True) # cannot be unique because double and single stranded are named with same integers
	label2 = models.CharField(max_length=20, blank=True)
	sequence = models.CharField(max_length=8, db_index=True, unique=True, validators=[validate_index_dna_sequence])
	
class Library(Timestamped):
	sample = models.ForeignKey(Sample, on_delete=models.PROTECT, null=True)
	extract = models.ForeignKey(Extract, on_delete=models.PROTECT, null=True)
	library_batch = models.ForeignKey(LibraryBatch, on_delete=models.CASCADE, null=True)
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
	
	# single stranded libraries have indices directly assigned
	p5_index = models.ForeignKey(P5_Index, on_delete=models.PROTECT, null=True)
	p7_index = models.ForeignKey(P7_Index, on_delete=models.PROTECT, null=True)
	# double stranded libraries have barcodes, and indices applied at capture
	p5_barcode = models.ForeignKey(Barcode, on_delete=models.PROTECT, null=True, related_name='p5_barcode')
	p7_barcode = models.ForeignKey(Barcode, on_delete=models.PROTECT, null=True, related_name='p7_barcode')
	
	def clean(self):
		super(Library, self).clean()
		if (self.p5_index is not None or self.p7_index is not None) and (self.p5_barcode is not None or self.p7_barcode is not None):
			raise ValidationError(_('Library cannot have both indices and barcodes. Single-stranded libraries should have only indices, and double-stranded libraries should have only barcodes.'))
		if self.p5_index is None and self.p7_index is None and self.p5_barcode is None and self.p7_barcode is None:
			raise ValidationError(_('Library must have either indices or barcodes')) 
			
	@staticmethod
	def spreadsheet_header():
		return ['well_position',
			'reich_lab_library_id',
			'p5_barcode',
			'p7_barcode',
			'nanodrop',
			'qpcr',
			'plate_id',
			'position'
			'barcode',
			'notes',
			#'storage_location',
			]
		
	def to_spreadsheet_row(self):
		layout_element = LibraryBatchLayout.objects.get(library_batch=self.library_batch, library=self)
		return [ str(layout_element),
			self.reich_lab_library_id,
			self.p5_barcode.label,
			self.p7_barcode.label,
			self.nanodrop,
			self.qpcr,
			self.plate_id,
			self.position,
			self.barcode,
			self.notes
			]
		
	def from_spreadsheet_row(self, headers, arg_array, user):
		reich_lab_library_id = arg_array[headers.index('reich_lab_library_id')]
		if self.reich_lab_library_id != reich_lab_library_id:
			raise ValueError(f'reich_lab_library_id mismatch {self.reich_lab_library_id} {reich_lab_library_id}')
		
		layout_element = LibraryBatchLayout.objects.get(library_batch=self.library_batch, library=self)
		position_from_sheet = arg_array[headers.index('well_position')]
		if str(layout_element) != position_from_sheet:
			raise ValueError(f'cannot change position of {reich_lab_library_id}')
			
		self.nanodrop = float(arg_array[headers.index('nanodrop')])
		self.qpcr = float(arg_array[headers.index('qpcr')])
		self.plate_id = arg_array[headers.index('plate_id')]
		self.position = arg_array[headers.index('position')]
		self.barcode = arg_array[headers.index('barcode')]
		self.notes = arg_array[headers.index('notes')]
		self.save(save_user=user)
	
	
# extract -> library
class LibraryBatchLayout(TimestampedWellPosition):
	library_batch = models.ForeignKey(LibraryBatch, on_delete=models.CASCADE, null=True)
	extract = models.ForeignKey(Extract, on_delete=models.CASCADE, null=True)
	control_type = models.ForeignKey(ControlType, on_delete=models.PROTECT, null=True)
	ul_extract_used = models.FloatField(null=True) # populated from library protocol, needs to done after layout elements are created
	notes = models.TextField(blank=True)
	library = models.ForeignKey(Library, on_delete=models.SET_NULL, null=True, help_text='')
	
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
	
class ShotgunPool(Timestamped):
	name = models.CharField(max_length=50)
	technician = models.CharField(max_length=10, blank=True)
	technician_fk = models.ForeignKey(WetLabStaff, on_delete=models.SET_NULL, null=True)
	date = models.DateField(null=True)
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
		
class SequencingRun(Timestamped):
	name = models.CharField(max_length=50, unique=True, db_index=True)
	technician = models.CharField(max_length=10, blank=True, default='')
	technician_fk = models.ForeignKey(WetLabStaff, on_delete=models.SET_NULL, null=True)
	date = models.DateField(null=True)
	sequencing = models.ForeignKey(SequencingPlatform, on_delete=models.SET_NULL, null=True)
	notes = models.TextField(blank=True, default='')
	
class ControlsExtract(Timestamped):
	lysate_batch = models.ForeignKey(LysateBatch, on_delete=models.PROTECT)
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
	mt_seq_run = models.ForeignKey(SequencingRun, null=True, on_delete=models.SET_NULL, related_name='results_mt')
	shotgun_pool = models.ForeignKey(ShotgunPool, null=True, on_delete=models.SET_NULL)
	shotgun_seq_run = models.ForeignKey(SequencingRun, null=True, on_delete=models.SET_NULL, related_name='results_shotgun')
	nuclear_capture_plate = models.ForeignKey(NuclearCapturePlate, null=True, on_delete=models.SET_NULL)
	nuclear_seq_run = models.ForeignKey(SequencingRun, null=True, on_delete=models.SET_NULL, related_name='results_nuclear')
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
