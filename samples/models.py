from django.db import models
from django.utils import timezone
from datetime import date

from django.contrib.auth.models import User

from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.utils.translation import gettext_lazy as _

from django.db.models import Max, Min, Count, Q
from django.db.models.signals import pre_delete
from django.dispatch import receiver

from .layout import PLATE_ROWS, PLATE_WELL_COUNT, PLATE_WELL_COUNT_HALF, validate_row_letter, plate_location, reverse_plate_location_coordinate, reverse_plate_location, duplicate_positions_check_db, p7_qbarcode_source, barcodes_for_location, indices_for_location, rotate_plate
from .sample_photos import num_sample_photos
from .spreadsheet import *
from .validation import *

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

def get_value(obj, *property_name_chain, default=''):
	current_object = obj
	for property_name in property_name_chain:
		if current_object is None:
			return default
		current_object = getattr(current_object, property_name)
		# resolve functions to objects to enable using methods in chain
		if callable(current_object):
			current_object = current_object()
	return current_object
		
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
		if self.pk is None:
			self.creation_timestamp = current_time
		self.modification_timestamp = current_time
		super(Timestamped, self).save(*args, **kwargs)
		
class TimestampedWellPosition(Timestamped):
	row = models.CharField(max_length=1, validators=[validate_row_letter], null=True)
	column = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(12)], null=True)
	
	class Meta:
		abstract = True
		
	def same_position(self, other_position):
		return self.row == other_position.row and self.column == other_position.column
	
	# This intentionally does not save the model so we can apply it to a temporary instance in memory
	def set_position(self, position_string):
		if len(position_string) > 0:
			self.row = position_string[0]
			self.column = int(position_string[1:])
		else:
			self.row = None
			self.column = None
	
	def __str__(self):
		row_str = f'{self.row}' if self.row else ''
		column_str =  f'{self.column}' if self.column else ''
		return f'{row_str}{column_str}'
		
	def clean(self):
		super(TimestampedWellPosition, self).clean()
		has_row = self.row is not None
		has_column = self.column is not None
		if (has_row and not has_column) or (not has_row and has_column):
			raise ValidationError(_('well positions cannot have only one of row and column specified')) 
	
	# rotate the plate by 180 degrees
	def rotate(self):
		row_index = PLATE_ROWS.index(self.row)
		self.column = (12 + 1) - self.column
		self.row = PLATE_ROWS[len(PLATE_ROWS) - row_index - 1]

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
	
	def name(self):
		return f'{self.first_name} {self.last_name}'
	
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
	
	def name(self):
		return f'{self.first_name} {self.last_name}'
	
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

class SkeletalElementCategory(models.Model):
	category = models.CharField(max_length=50, blank=True)
	sort_order = models.PositiveSmallIntegerField(default=1, help_text='For changing display order of categories in web interface')

class Sample(Timestamped):
	reich_lab_id = models.PositiveIntegerField(db_index=True, null=True, help_text=' assigned when a sample is selected from the queue by the wetlab')
	control = models.CharField(max_length=2, blank=True, help_text='Non-empty value indicates this is a control')
	queue_id = models.PositiveIntegerField(db_index=True, unique=True, null=True)
	
	collaborator = models.ForeignKey(Collaborator, on_delete=models.PROTECT, null=True)
	shipment = models.ForeignKey(Shipment, on_delete=models.PROTECT, null=True)
	return_id = models.ForeignKey(Return, on_delete=models.PROTECT, null=True)
	
	location_fk = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True)
	periods = models.ManyToManyField(Period)
	cultures = models.ManyToManyField(Culture)
	publications = models.ManyToManyField(Publication)

	individual_id = models.CharField(max_length=15, blank=True)
	
	skeletal_element = models.CharField(max_length=50, blank=True, help_text='Type of bone sample submitted for aDNA analysis')
	skeletal_element_category = models.ForeignKey(SkeletalElementCategory, null=True, on_delete=models.PROTECT)
	skeletal_code = models.CharField(max_length=150, blank=True, help_text='Sample identification code assigned by the collaborator')
	skeletal_code_renamed = models.TextField(blank=True, help_text='Sample identification code assigned by the Reich Lab')
	sample_date = models.TextField(blank=True, help_text='Age of sample; either a radiocarbon date or a date interval.')
	average_bp_date = models.FloatField(null=True, help_text='Average Before Present date, calculated from average of calibrated date range after conversion to BP dates')
	date_fix_flag = models.TextField(help_text='Flag for any issues with the date information submitted by the collaborator', blank=True)
	group_label = models.CharField(max_length=100, blank=True, help_text='Country_Culture_Period of Individual')
	period = models.CharField(max_length=50, blank=True, help_text='Archaeologic period component of group label of an Individual')
	culture = models.CharField(max_length=50, blank=True, help_text='Archaeologic culture component of group label of an Individual')
	outlier = models.CharField(max_length=50, blank=True, help_text='Outlier designation component of group label of an Individual')
	locality = models.CharField(max_length=150, blank=True, help_text='Location where skeletal remains were found')
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
	approved_negative_results = models.BooleanField(default=False, help_text='Approved for full reporting of negative results and photographs')
	approved_photo_sharing = models.BooleanField(null=True, help_text='Approved for sharing sample photographs. Null indicates unknown.')
	
	class Meta:
		unique_together = ['reich_lab_id', 'control']
		
	def assign_reich_lab_sample_number(self, **kwargs):
		if self.reich_lab_id is None:
			max_sample_number = Sample.objects.all().aggregate(Max('reich_lab_id'))['reich_lab_id__max']
			next_sample_number = max_sample_number + 1
			self.reich_lab_id = next_sample_number
			self.individual_id = f'I{self.reich_lab_id:04d}'
			self.save(**kwargs)
		return self.reich_lab_id
	
	def is_control(self):
		return len(self.control) > 0
	
	def __str__(self):
		return f'S{self.reich_lab_id:04d}{self.control}'
		
	def num_existing_photos(self):
		if self.reich_lab_id:
			return num_sample_photos(self.reich_lab_id)
		else:
			return 0
			
	def get_country(self):
		try:
			return self.location_fk.country
		except:
			return None
			
	def location_str(self):
		return f'{self.locality} {get_value(self.get_country(), "country_name")}'
			
	# 1. Used to generate extract object for an external sample received as an extract.
	# 2. Used for library negative controls starting at the library batch step. 
	# Any sample should only have one of these. Additional extracts will be recognized as duplicate after genotyping. 
	def originating_extract(self, extraction_lab):
		self.assign_reich_lab_sample_number()
		try:
			extract = Extract.objects.get(sample=self)
		except Extract.DoesNotExist: # 
			extract_id = f'{str(self)}.E1'
			extract = Extract.objects.create(extract_id=extract_id,
					reich_lab_extract_number=1,
					sample=self,
					extract_batch=None,
					extraction_lab=extraction_lab)
		return extract
		
		
class SamplePrepProtocol(Timestamped):
	preparation_method = models.CharField(max_length=50, help_text='Method used to produce bone powder')
	manuscript_summary = models.TextField(blank=True, help_text='Sampling method summary for manuscripts')
	protocol_reference = models.TextField(blank=True, help_text='Protocol citation')
	notes = models.TextField(blank=True, help_text='Notes about the method used to create bone powder')
	
def get_status_string(status_value, STATES):
	for candidate, string in STATES:
		if candidate == status_value:
			return string
	return 'Unknown'
	
class PowderBatch(Timestamped):
	name = models.CharField(max_length=50, unique=True)
	date = models.DateField(null=True, help_text='Date batch was powdered')
	technician = models.CharField(max_length=50, blank=True)
	technician_fk = models.ForeignKey(WetLabStaff, on_delete=models.SET_NULL, null=True)
	notes = models.TextField(blank=True)
	STOP = 1000
	OPEN = 0
	IN_PROGRESS = 100
	READY_FOR_PLATE = 200
	CLOSED = 300
	
	POWDER_BATCH_STATES = (
		(STOP, 'Stop'),
		(OPEN, 'Open'),
		(IN_PROGRESS, 'In Progress'),
		(READY_FOR_PLATE, 'Ready For Plate'),
		(CLOSED, 'Closed')
	)
	status = models.SmallIntegerField(null=True, default = OPEN, choices=POWDER_BATCH_STATES)
	
	# return string representing status. For templates
	def get_status(self):
		return get_status_string(self.status, self.POWDER_BATCH_STATES)
		
	def assign_sample_prep_queue_entries(self, sample_prep_ids, user):
		failed_assignments = {}
		# first clear powder batch
		to_clear = SamplePrepQueue.objects.filter(powder_batch=self).exclude(id__in=sample_prep_ids)
		for sample_prep_entry in to_clear:
			sample_prep_entry.powder_batch = None
			# existing powder sample is destroyed for this sample prep entry
			if sample_prep_entry.powder_sample != None:
				# in models, powder sample is protected if there is a lysate
				# sample prep entry sets reference to null
				sample_prep_entry.powder_sample.delete()
			if sample_prep_entry.prepared_powder != None:
				sample_prep_entry.prepared_powder.delete()
			sample_prep_entry.save(save_user=user)
		# add samples prep queue entries to powder batch
		for sample_prep_entry in SamplePrepQueue.objects.filter(id__in=sample_prep_ids):
			existing_powder_batch = sample_prep_entry.powder_batch
			if existing_powder_batch == None or existing_powder_batch == self:
				sample_prep_entry.powder_batch = self
				sample_prep_entry.save(save_user=user)
				if sample_prep_entry.powder_sample != None:
					powder_sample = sample_prep_entry.powder_sample
					powder_sample.powder_batch = self
					powder_sample.save(save_user=user)
			else: # already assigned elsewhere
				failed_assignments[sample_prep_entry.id] = sample_prep_entry.powder_batch.name
		# assign reich lab sample number
		# Open is the state where samples can be added. If it is not open, then create the powder sample and assign Reich lab sample number
		if self.status not in [self.OPEN, self.STOP]:
			for sample_prep_entry in SamplePrepQueue.objects.filter(powder_batch=self).order_by('id'):
				sample_prep_entry.new_reich_lab_powder_sample(user)
		return failed_assignments
		
	def assign_powder_prep_queue_entries(self, powder_prep_ids, user):
		# remove unassigned entries
		to_clear = PowderPrepQueue.objects.filter(powder_batch=self).exclude(id__in=powder_prep_ids)
		for powder_prep_entry in to_clear:
			if powder_prep_entry.prepared_powder != None:
				powder_prep_entry.prepared_powder.delete()
			powder_prep_entry.powder_batch = None
			powder_prep_entry.save(save_user=user)
		# assign entries
		for powder_prep_entry in PowderPrepQueue.objects.filter(id__in=powder_prep_ids):
			existing_powder_batch = powder_prep_entry.powder_batch
			if existing_powder_batch == None or existing_powder_batch == self:
				powder_prep_entry.powder_batch = self
				powder_prep_entry.save(save_user=user)
		# Open is the state where samples can be added. If it is not open, then create the powder sample and assign Reich lab sample number
		if self.status not in [self.OPEN, self.STOP]:
			for powder_prep_entry in PowderPrepQueue.objects.filter(powder_batch=self).order_by('id'):
				powder_prep_entry.new_reich_lab_powder_sample(user)
	
	# modify powder samples from spreadsheet
	# it would be better to reuse form validation
	def powder_samples_from_spreadsheet(self, spreadsheet_file, user):
		headers, data_rows = spreadsheet_headers_and_data_rows(spreadsheet_file)
		powder_samples = PowderSample.objects.filter(powder_batch=self)
		if headers[0] != 'powder_sample_id-':
			raise ValueError('powder_sample_id is not first')
			
		for line in data_rows:
			fields = re.split('\t', line)
			powder_sample_id = fields[0]
			if len(powder_sample_id) > 0:
				print(powder_sample_id)
				powder_sample = powder_samples.get(powder_sample_id=powder_sample_id)
				powder_sample.from_spreadsheet_row(headers[1:], fields[1:], user)
				
	# Return number of lysate batch wells that have powder from this batch. Missing and unassigned powders have a LysateBatchLayout object with null lysate batch and do not count. 
	# If a powder sample appears in 2 wells, this counts as 2. 
	def number_plated_powder_samples(self):
		elements = LysateBatchLayout.objects.filter(powder_batch=self, lysate_batch__isnull=False, is_lost=False, control_type__isnull=True, powder_sample__isnull=False)
		return len(elements)
		
	# close status if all powders have been assigned and status is ready to plate
	# ready to plate status if status was closed but not all powders are assigned
	def close_if_finished(self, any_status=False):
		expected_samples_from_bone = SamplePrepQueue.objects.filter(powder_batch=self).count()
		expected_samples_from_powder = PowderPrepQueue.objects.filter(powder_batch=self).count()
		expected = expected_samples_from_bone + expected_samples_from_powder
		
		assigned = self.number_plated_powder_samples()
		if assigned == expected and expected > 0:
			if any_status or self.status == self.READY_FOR_PLATE:
				self.status = self.CLOSED
				self.save()
		elif assigned > expected and expected > 0:
			raise ValueError(f'more powder samples plated than available {assigned} {expected}')
		elif assigned < expected and (self.status == self.CLOSED):
			self.status = self.READY_FOR_PLATE
			self.save()
		return assigned

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
	def spreadsheet_header(cumulative=False):
		headers = ['powder_sample_id-',
			'skeletal_element_category',
			'sampling_notes',
			'total_powder_produced_mg',
			'powder_for_extract',
			'storage_location',
			'sample_prep_lab',
			'sample_prep_protocol',
			'shipment_name-',
			'collaborator_id-',
			'group_label-',
			'notes-',
			'notes2-',
			'location-',
			]
		if cumulative:
			headers += queue_spreadsheet_header()
		return headers
		
	# for wetlab spreadsheet, return array to output as tsv
	# order corresponds to the spreadsheet header
	def to_spreadsheet_row(self, cumulative=False):
		preparation_method = self.sample_prep_protocol.preparation_method if self.sample_prep_protocol else ''
		shipment_name = self.sample.shipment.shipment_name if self.sample.shipment else ''
		values = [self.powder_sample_id,
			get_value(self.sample.skeletal_element_category, 'category'),
			self.sampling_notes,
			self.total_powder_produced_mg,
			self.powder_for_extract,
			self.storage_location,
			self.sample_prep_lab,
			preparation_method,
			shipment_name,
			csv_text_escape(self.sample.skeletal_code),
			self.sample.group_label,
			self.sample.notes,
			self.sample.notes_2,
			self.sample.location_str(),
		]
		if cumulative:
			prep_entry = None
			try:
				prep_entry = SamplePrepQueue.objects.get(sample=self.sample, powder_batch=self.powder_batch)
			except SamplePrepQueue.DoesNotExist:
				try:
					prep_entry = PowderPrepQueue.objects.get(sample=self.sample, powder_batch=self.powder_batch)
				except PowderPrepQueue.DoesNotExist:
					pass
			values += queue_to_spreadsheet_row(prep_entry, self.sample)
		return values
		
	# from wetlab spreadsheet
	def from_spreadsheet_row(self, headers, arg_array, user):
		skeletal_element_category = arg_array[headers.index('skeletal_element_category')]
		if self.sample.skeletal_element_category.category != skeletal_element_category:
			self.sample.skeletal_element_category = SkeletalElementCategory.objects.get(category=skeletal_element_category)
			self.sample.save(save_user=user)
		
		self.sampling_notes = arg_array[headers.index('sampling_notes')]
		self.total_powder_produced_mg = float( arg_array[headers.index('total_powder_produced_mg')])
		self.powder_for_extract = float(arg_array[headers.index('powder_for_extract')])
		self.storage_location = arg_array[headers.index('storage_location')]
		self.sample_prep_lab = arg_array[headers.index('sample_prep_lab')]
		
		preparation_method = arg_array[headers.index('sample_prep_protocol')]
		self.sample_prep_protocol = SamplePrepProtocol.objects.get(preparation_method=preparation_method)
		self.save(save_user=user)
	
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

# a control layout is applied to batch layouts to add controls
class ControlLayout(TimestampedWellPosition):
	control_set = models.ForeignKey(ControlSet, on_delete=models.CASCADE)
	control_type = models.ForeignKey(ControlType, on_delete=models.PROTECT)
	active = models.BooleanField(default=True)
	notes = models.TextField(blank=True)

EXTRACT_NEGATIVE = 'Extract Negative'
LIBRARY_NEGATIVE = 'Library Negative'
LIBRARY_POSITIVE = 'Library Positive'

EXTRACT_AND_LIBRARY_CONTROLS = [EXTRACT_NEGATIVE, LIBRARY_NEGATIVE, LIBRARY_POSITIVE]

PCR_NEGATIVE = 'PCR Negative'
CAPTURE_POSITIVE = 'Capture Positive'
CAPTURE_POSITIVE_LIBRARY_NAME_DS = 'capture_positive_ds'

# find the Reich Lab sample number associated with a layout element
# Lookup depends on the type of layout element
# For new style of control naming where we do not assign Reich lab sample numbers, the proper result is None
def control_sample_number_from_layout_element(control_layout_element):
	reich_lab_sample_number = None
	if control_layout_element.control_type is None:
		raise ValueError('Not a control')
	if isinstance(control_layout_element, LysateBatchLayout):
		if control_layout_element.powder_sample and control_layout_element.powder_sample.sample:
			reich_lab_sample_number = control_layout_element.powder_sample.sample.reich_lab_id
	elif isinstance(control_layout_element, ExtractionBatchLayout):
		if control_layout_element.lysate and control_layout_element.lysate.powder_sample and control_layout_element.lysate.powder_sample.sample:
			reich_lab_sample_number = control_layout_element.lysate.powder_sample.sample.reich_lab_id
	else:
		raise ValueError('Unhandled class')
	return reich_lab_sample_number

# extract negative and library negative controls get Reich lab sample numbers
# find the sample number for one of these types from lysate batch layout elements
def control_sample_number(control_element_queryset):
	reich_lab_sample_number = None
	for control_layout_element in control_element_queryset:
		current_sample_number = control_sample_number_from_layout_element(control_layout_element)
		if reich_lab_sample_number is None:
			reich_lab_sample_number = current_sample_number
		elif reich_lab_sample_number != current_sample_number:
			raise ValueError(f'Multiple control sample ids: {reich_lab_sample_number} {current_sample_number}')
	return reich_lab_sample_number
	
# We are discontinuing use of Reich lab sample number assignments for controls. 
# This is the replacement name
# Each control needs a distinct name, so we assign an index based on the number of existing products that exist
def control_name_string(batch_name, control_type, num_existing):
	# remove _LY from batch name, if present
	if batch_name.endswith('_LY') or batch_name.endswith('_RE') or batch_name.endswith('_DS') or batch_name.endswith('_SS'):
		batch_name = batch_name[:-3]
	# lowercase control negative type
	control_type_str = control_type.control_type
	if control_type_str == EXTRACT_NEGATIVE:
		short_control_str = 'extract'
	elif control_type_str == LIBRARY_NEGATIVE:
		short_control_str = 'library'
	else:
		raise ValueError(f'Unhandled control type {control_type_str}')
		
	return f'control_{short_control_str}_{num_existing+1}_{batch_name}'
	
# How many lysates are there for this sample
def lysates_for_sample(sample):
	existing_lysates = Lysate.objects.filter(powder_sample__sample=sample)
	return len(existing_lysates)

# this creates a lysate for a layout_element if it does not exist, and returns the existing one otherwise
def create_lysate(lysate_layout_element, lysate_batch, user):
	# library positive controls do not generate lysates
	if lysate_layout_element.control_type == ControlType.objects.get(control_type=LIBRARY_POSITIVE):
		return None
	# only create the lysate from powder for this well once
	elif lysate_layout_element.lysate is not None:
		return lysate_layout_element.lysate
	else:
		sample = None
		powder_sample = lysate_layout_element.powder_sample
		next_lysate_number = 1
		# lysate name starting from a sample
		if powder_sample:
			if powder_sample:
				sample = powder_sample.sample
				next_lysate_number = lysates_for_sample(powder_sample.sample) +1
				prior_id = str(sample)
			else:
				raise ValueError(f'powder sample without sample {powder_sample.powder_sample_id}')
		else: # lysate name for a control
			num_existing_lysates_for_control_type = LysateBatchLayout.objects.filter(lysate_batch=lysate_batch, control_type=lysate_layout_element.control_type, powder_sample=None, lysate__isnull=False).count()
			prior_id = control_name_string(lysate_batch.batch_name, lysate_layout_element.control_type, num_existing_lysates_for_control_type)
			lysate_id = ''
		lysate_id = f'{prior_id}.Y{next_lysate_number}'
		print(f'created lysate id {lysate_id} {lysate_layout_element}')
		# library negatives have no lysis volume
		is_library_negative = (lysate_layout_element.control_type is not None) and (lysate_layout_element.control_type.control_type == LIBRARY_NEGATIVE)
		total_volume_produced = lysate_batch.protocol.total_lysis_volume if not is_library_negative else 0
		powder_used_mg = powder_sample.powder_for_extract if powder_sample else 0
		lysate = Lysate(lysate_id=lysate_id,
					reich_lab_lysate_number=next_lysate_number,
					powder_sample=powder_sample,
					sample=sample,
					lysate_batch=lysate_batch,
					powder_used_mg=powder_used_mg,
					total_volume_produced=total_volume_produced)
		lysate.save(save_user=user)
		lysate_layout_element.lysate = lysate
		lysate_layout_element.save(save_user=user)
		
		return lysate
		
# reused at least for LysateBatch and ExtractionBatch
# find sample numbers used for existing controls
# remove all controls (in preparation for readding with new layout)
# existing_controls is a queryset of layout for a batch
def existing_controls_cleanup(existing_controls, user):
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
	
	return extract_negative_sample_id, library_negative_sample_id

# turn powders into lysates
class LysateBatch(Timestamped):
	batch_name = models.CharField(max_length=50, unique=True, help_text='Usually ends with _LY')
	protocol = models.ForeignKey(ExtractionProtocol, on_delete=models.PROTECT, null=True)
	technician = models.CharField(max_length=50, blank=True)
	technician_fk = models.ForeignKey(WetLabStaff, on_delete=models.SET_NULL, null=True)
	date = models.DateField(null=True)
	robot = models.CharField(max_length=20, blank=True)
	note = models.TextField(blank=True)
	layout = models.ManyToManyField(PowderSample, through='LysateBatchLayout', related_name='powder_sample_assignment')
	control_set = models.ForeignKey(ControlSet, on_delete=models.SET_NULL, null=True)
	
	OPEN = 0
	IN_PROGRESS = 100
	CLOSED = 200
	STOP = 1000
	
	LYSATE_BATCH_STATES = (
		(OPEN, 'Open'),
		(IN_PROGRESS, 'In progress'),
		(CLOSED, 'Closed'),
		(STOP, 'Stop')
	)
	status = models.PositiveSmallIntegerField(default = OPEN, choices=LYSATE_BATCH_STATES)
	
	# return string representing status. For templates
	def get_status(self):
		for state_int, state_name in self.LYSATE_BATCH_STATES:
			if state_int == self.status:
				return state_name
		raise ValueError(f'No lysate batch status {self.status}')
		
	# retain only powder samples in layout_element_ids
	# in addition, preserve controls
	# update status for affected powder batches
	def restrict_layout_elements(self, layout_element_ids, user):
		to_remove = LysateBatchLayout.objects.filter(lysate_batch=self).exclude(id__in=layout_element_ids).exclude(control_type__isnull=False)
		for layout_element in to_remove:
			layout_element.lysate_batch = None
			layout_element.save(save_user=user)
		
		powder_batch_ids = [x.powder_sample.powder_batch.id for x in to_remove]
		for powder_batch in PowderBatch.objects.filter(id__in=powder_batch_ids):
			powder_batch.close_if_finished()
	
	# assign LysateBatchLayout elements
	def assign_powder_samples(self, layout_element_ids, user):
		DEFAULT_ROW = 'A'
		DEFAULT_COLUMN = 1
		print(f'assign_powder_samples layout_element_ids {layout_element_ids}')
		
		powder_batch_ids = [] # to update powder batch status
		for lysate_batch_layout in LysateBatchLayout.objects.filter(id__in=layout_element_ids):
			lysate_batch_layout.lysate_batch = self
			if lysate_batch_layout.row is None:
				lysate_batch_layout.row = DEFAULT_ROW
			if lysate_batch_layout.column is None:
				lysate_batch_layout.column = DEFAULT_COLUMN
			lysate_batch_layout.save(save_user = user)
			
			if lysate_batch_layout.powder_sample.powder_batch not in powder_batch_ids:
				powder_batch_ids.append(lysate_batch_layout.powder_sample.powder_batch.id)
			
		# update status of powder batches for new samples
		for powder_batch in PowderBatch.objects.filter(id__in=powder_batch_ids):
			powder_batch.close_if_finished()
			
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
		# examine existing controls for sample numbers
		extract_negative_sample_id, library_negative_sample_id = existing_controls_cleanup(existing_controls, user)
		
		# create new control layout entries
		extract_negative_control_count = 0
		library_negative_control_count = 0
		for control in controls:
			layout_element = LysateBatchLayout(lysate_batch=self, control_type=control.control_type, row=control.row, column=control.column, powder_used_mg=0)
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
		control_type = ControlType.objects.get(control_type=LIBRARY_NEGATIVE)
		
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
				layout_element = LysateBatchLayout(lysate_batch=self, control_type=control_type, row=row, column=column, powder_used_mg=0, powder_sample=None)
				layout_element.save(save_user=user)
				
	def create_lysates(self, user):
		layout = LysateBatchLayout.objects.filter(lysate_batch=self).order_by('row', 'column')
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
		layout_elements = LysateBatchLayout.objects.filter(lysate_batch=self)
		headers, data_rows = spreadsheet_headers_and_data_rows(spreadsheet)
		
		for line in data_rows:
			fields = re.split('\t', line)
			
			well_position = get_spreadsheet_value(headers, fields, 'well_position-')
			#print(well_position)
			temp = TimestampedWellPosition()
			temp.set_position(well_position)
			
			layout_element = layout_elements.get(column=temp.column, row=temp.row)
			layout_element.from_spreadsheet_row(headers, fields, user)

class Lysate(Timestamped):
	lysate_id = models.CharField(max_length=50, unique=True, null=False, db_index=True)
	reich_lab_lysate_number = models.PositiveIntegerField(null=True, help_text='Starts at 1 for each sample.')
	powder_sample = models.ForeignKey(PowderSample, null=True, on_delete=models.PROTECT) # if this is null, it's a control
	lysate_batch = models.ForeignKey(LysateBatch, null=True, on_delete=models.CASCADE)
	storage = models.ForeignKey(Storage, on_delete=models.PROTECT, null=True)
	sample = models.ForeignKey(Sample, on_delete=models.PROTECT, null=True)
	
	powder_used_mg = models.FloatField(null=True, help_text='milligrams of bone powder used in lysis')
	total_volume_produced = models.FloatField(null=True, help_text='Total microliters of lysate produced')
	
	plate_id = models.CharField(max_length=12, blank=True, help_text='FluidX rack barcode')
	position = models.CharField(max_length=3, blank=True, help_text='well/tube position in plate/rack')
	barcode = models.CharField(max_length=12, blank=True, help_text='Physical barcode on FluidX tube')
	notes = models.TextField(blank=True)
	
	def clean(self):
		super(Lysate, self).clean()
		# make sure sample is consistent
		if self.powder_sample and self.powder_sample.sample != self.sample:
			raise ValidationError(_('lysate sample is inconsistent with powder sample'))
	
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
		
	# return the highest extract number for this lysate
	# This is not equivalent to how many extracts there are because there are extracts with the number 0. These appear to be failures that were renumbered after failure. 
	def highest_extract(self):
		max_value = Extract.objects.filter(lysate=self).aggregate(Max('reich_lab_extract_number', default=0))['reich_lab_extract_number__max']
		if max_value:
			return max_value
		else:
			return 0
			
	# the direct sample link is validated in clean to be consistent with powder sample 
	def get_sample(self):
		return self.sample
	
# powder -> lysate
# This holds powder that has been weighed in preparation for lysate creation, or lost powder
class LysateBatchLayout(TimestampedWellPosition):
	lysate_batch = models.ForeignKey(LysateBatch, on_delete=models.CASCADE, null=True)
	powder_sample = models.ForeignKey(PowderSample, on_delete=models.CASCADE, null=True)
	control_type = models.ForeignKey(ControlType, on_delete=models.PROTECT, null=True)
	powder_used_mg = models.FloatField(null=True)
	notes = models.TextField(blank=True)
	lysate = models.ForeignKey(Lysate, on_delete=models.SET_NULL, null=True, help_text='Lysate created in this well from powder')
	is_lost = models.BooleanField(default=False)
	powder_batch = models.ForeignKey(PowderBatch, on_delete=models.CASCADE, null=True, help_text='Powder batch where powder was weighed')
	
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
		if self.is_lost and self.lysate_batch is not None:
			raise ValidationError(_('Lost powder cannot have lysate batch.'))
			
	@staticmethod
	def spreadsheet_header(cumulative=False):
		headers = ['well_position-', 
			'lysate_id-',
			'collaborator_id-',
			'powder_batch_name-',
			'powder_used_mg',
			'total_volume_produced',
			'plate_id',
			'barcode',
			'notes']
		if cumulative:
			headers += PowderSample.spreadsheet_header(cumulative)
		return headers
		
	def to_spreadsheet_row(self, cumulative=False):
		values = []
		values.append(str(self))
		
		values.append(get_value(self.lysate, 'lysate_id'))
		
		collaborator_id = csv_text_escape(self.powder_sample.sample.skeletal_code) if self.powder_sample else ''
		values.append(collaborator_id)
		
		powder_batch_name = self.powder_sample.powder_batch.name if (self.powder_sample and self.powder_sample.powder_batch) else ''
		values.append(powder_batch_name)
		
		values.append(get_value(self.lysate, 'powder_used_mg'))
		values.append(get_value(self.lysate, 'total_volume_produced'))
		values.append(get_value(self.lysate, 'plate_id'))
		values.append(get_value(self.lysate, 'barcode'))
		values.append(get_value(self.lysate, 'notes'))
		
		if cumulative:
			additional_values = None
			if self.powder_sample:
				additional_values = self.powder_sample.to_spreadsheet_row(cumulative)
			else:
				additional_values = empty_values(PowderSample.spreadsheet_header(cumulative))
			values += additional_values
		
		return values
		
	def from_spreadsheet_row(self, headers, arg_array, user):
		row_lysate_id = arg_array[headers.index('lysate_id-')]
		if self.lysate:
			lysate = self.lysate
			if lysate.lysate_id != row_lysate_id:
				raise ValueError(f'lysate_id mismatch {lysate.lysate_id} {row_lysate_id}')
			lysate.powder_used_mg = float(arg_array[headers.index('powder_used_mg')])
			lysate.total_volume_produced = float(arg_array[headers.index('total_volume_produced')])
			lysate.plate_id = arg_array[headers.index('plate_id')]
			lysate.barcode = arg_array[headers.index('barcode')]
			lysate.notes = arg_array[headers.index('notes')]
			lysate.save(save_user=user)
		
@receiver(pre_delete, sender=LysateBatchLayout, dispatch_uid='lysatebatchlayout_delete_signal')
def delete_dependent_lysate(sender, instance, using, **kwargs):
	if instance.lysate:
		instance.lysate.delete()
		
# common header for table starting from either samples or powders
def queue_spreadsheet_header():
	return [
		'Priority',
		'Expected Complexity',
		'Sampling Tech',
		'Sample Prep Lab',
		'UDG',
		'Shipment ID',
		'Collaborator',
		'Skeletal Element',
		'Skeletal Code',
		'Country',
		'Region',
		'Period',
		'Culture',
		'Notes',
		'Notes2',
		'Prep ID'
		]
		
# This could be rolled into an abstract base class for the SamplePrepQueue and PowderPrepQueue, but it should still work as a function and definitely does not require migrations this way
# For cumulative data, we need to produce the same data available for a queue when only a sample is available
def queue_to_spreadsheet_row(queue_item, sample=None):
	if sample and queue_item and queue_item.sample != sample:
		raise ValueError(f'Two samples {queue_item.sample.id} {sample.id}')
	elif sample is None: # the default case where we have queue_item entry
		sample = queue_item.sample
	
	name = get_value(sample, 'collaborator', 'name')
	preparation_method = get_value(queue_item, 'sample_prep_protocol', 'preparation_method')
	country = sample.get_country()

	if hasattr(queue_item, 'sample_prep_lab'):
		prep_lab = get_value(queue_item, 'sample_prep_lab')
	else: # bone samples are handled in house
		prep_lab = REICH_LAB
	
	return [
		get_value(queue_item, 'priority'),
		get_value(sample.expected_complexity, 'description'),
		preparation_method,
		prep_lab,
		get_value(queue_item, 'udg_treatment'),
		get_value(sample.shipment, 'shipment_name'),
		name,
		sample.skeletal_element,
		csv_text_escape(sample.skeletal_code),
		get_value(country, 'country_name'),
		get_value(country, 'region'),
		sample.period,
		sample.culture,
		sample.notes,
		sample.notes_2,
		get_value(queue_item, 'id'),
	]
		
# Wetlab consumes samples from this queue for powder batches
class SamplePrepQueue(Timestamped):
	priority = models.SmallIntegerField(help_text='Lower is higher priority')
	sample = models.ForeignKey(Sample, on_delete=models.CASCADE)
	sample_prep_protocol = models.ForeignKey(SamplePrepProtocol, on_delete=models.SET_NULL, null=True)
	udg_treatment = models.CharField(max_length=10)
	powder_batch = models.ForeignKey(PowderBatch, null=True, on_delete=models.SET_NULL,)
	powder_sample = models.ForeignKey(PowderSample, null=True, on_delete=models.SET_NULL) # needed to unassign
	prepared_powder = models.ForeignKey(LysateBatchLayout, on_delete=models.SET_NULL, null=True)
	
	# create a PowderSample and assign Reich Lab Sample Number
	def new_reich_lab_powder_sample(self, user):
		SAMPLE_PREP_LAB = 'Reich Lab'
		sample = self.sample
		# if the corresponding sample does not have Reich Lab sample number, then assign it the next one
		if sample.reich_lab_id is None:
			sample.assign_reich_lab_sample_number()
		try:
			if self.powder_sample != None:
				powder_sample = self.powder_sample
			else:
				powder_sample = PowderSample.objects.get(sample=sample, powder_batch=self.powder_batch)
		except PowderSample.DoesNotExist:
			# count how many powder samples for this sample
			existing_powder_samples = PowderSample.objects.filter(sample=sample)
			powder_sample_int = existing_powder_samples.count() + 1
			
			powder_sample_id = f'S{sample.reich_lab_id}.P{powder_sample_int}'
			powder_sample = PowderSample.objects.create(sample=sample, powder_batch=self.powder_batch, powder_sample_id=powder_sample_id)
		powder_sample.sample_prep_protocol=self.sample_prep_protocol
		powder_sample.sample_prep_lab=SAMPLE_PREP_LAB
		powder_sample.save_user = user
		powder_sample.save()
		
		# LysateBatchLayout element for assignment to LysateBatch
		# This represents a tube with powder weighed
		try:
			# do not lookup with powder batch because this was added later
			prepared_powder = LysateBatchLayout.objects.get(lysate_batch=None, powder_sample=powder_sample, control_type=None, lysate=None)
		except LysateBatchLayout.DoesNotExist:
			prepared_powder = LysateBatchLayout(lysate_batch=None, powder_sample=powder_sample, control_type=None, lysate=None, powder_batch=self.powder_batch)
			prepared_powder.save(save_user=user)
		
		self.prepared_powder = prepared_powder
		self.powder_sample = powder_sample
		self.save_user = user
		self.save()
	
	@staticmethod
	def spreadsheet_header():
		return queue_spreadsheet_header()
		
	# for wetlab spreadsheet, return array to output as tsv
	# order corresponds to the spreadsheet header
	def to_spreadsheet_row(self):
		return queue_to_spreadsheet_row(self)
		
class PowderPrepQueue(Timestamped):
	priority = models.SmallIntegerField(help_text='Lower is higher priority')
	sample = models.ForeignKey(Sample, on_delete=models.CASCADE)
	powder_sample = models.ForeignKey(PowderSample, on_delete=models.SET_NULL, null=True)
	udg_treatment = models.CharField(max_length=10)
	powder_batch = models.ForeignKey(PowderBatch, null=True, on_delete=models.SET_NULL, help_text='Powder batch where weighed for lysate')
	prepared_powder = models.ForeignKey(LysateBatchLayout, on_delete=models.SET_NULL, null=True)
	sample_prep_protocol = models.ForeignKey(SamplePrepProtocol, on_delete=models.SET_NULL, null=True)
	sample_prep_lab = models.CharField(max_length=50, blank=True, help_text='Name of lab where bone powder was produced')
	
	# this always creates a new object for assignment to LysateBatch, in case we want more than one lysate for the sample powder sample
	def create_prepared_powder(self, user):
		self.powder_sample.sample.assign_reich_lab_sample_number()
		# LysateBatchLayout element for assignment to LysateBatch
		# This represents a tube with powder weighed
		prepared_powder = LysateBatchLayout(lysate_batch=None, powder_sample=powder_sample, control_type=None, lysate=None)
		prepared_powder.save(save_user=user)
		self.prepared_powder = prepared_powder
		self.save(save_user=user)
		
	# create a PowderSample and assign Reich Lab Sample Number
	def new_reich_lab_powder_sample(self, user):
		if self.powder_batch is None:
			raise ValueError('Cannot create from PowderPrepQueue objects without powder batch')
		# if the corresponding sample does not have Reich Lab sample number, then assign it the next one
		self.sample.assign_reich_lab_sample_number()
		
		try:
			if self.powder_sample != None:
				powder_sample = self.powder_sample
			else:
				powder_sample = PowderSample.objects.get(sample=self.sample, powder_batch=self.powder_batch)
		except PowderSample.DoesNotExist: # create a powder sample entry
			# count how many powder samples for this sample
			existing_powder_samples = PowderSample.objects.filter(sample=self.sample)
			powder_sample_int = existing_powder_samples.count() + 1
			
			powder_sample_id = f'S{self.sample.reich_lab_id}.P{powder_sample_int}'
			powder_sample = PowderSample.objects.create(sample=self.sample, powder_batch=self.powder_batch, powder_sample_id=powder_sample_id)
		powder_sample.sample_prep_protocol=self.sample_prep_protocol
		powder_sample.sample_prep_lab = self.sample_prep_lab
		powder_sample.save(save_user=user)
		
		# LysateBatchLayout element for assignment to LysateBatch
		# This represents a tube with powder weighed
		try:
			prepared_powder = LysateBatchLayout.objects.get(lysate_batch=None, powder_sample=powder_sample, control_type=None, lysate=None, powder_batch=self.powder_batch)
		except LysateBatchLayout.DoesNotExist:
			prepared_powder = LysateBatchLayout(lysate_batch=None, powder_sample=powder_sample, control_type=None, lysate=None, powder_batch=self.powder_batch)
			prepared_powder.save(save_user=user)
		
		self.prepared_powder = prepared_powder
		self.powder_sample = powder_sample
		self.save_user = user
		self.save()
	
	@staticmethod
	def spreadsheet_header():
		return queue_spreadsheet_header()
		
	def to_spreadsheet_row(self):
		return queue_to_spreadsheet_row(self)
	
class ExtractionBatch(Timestamped):
	batch_name = models.CharField(max_length=50, unique=True, help_text='Usually ends with _RE')
	protocol = models.ForeignKey(ExtractionProtocol, on_delete=models.PROTECT, null=True)
	technician = models.CharField(max_length=50, blank=True)
	technician_fk = models.ForeignKey(WetLabStaff, on_delete=models.SET_NULL, null=True)
	date = models.DateField(null=True)
	robot = models.CharField(max_length=20, blank=True)
	note = models.TextField(blank=True)
	layout = models.ManyToManyField(Lysate, through='ExtractionBatchLayout', related_name='lysate_assignment')
	control_set = models.ForeignKey(ControlSet, on_delete=models.SET_NULL, null=True)
	rotated = models.BooleanField(default=False, help_text='True for second extract plates that are rotated 180 degrees')
	
	OPEN = 0
	IN_PROGRESS = 100
	CLOSED = 200
	STOP = 1000
	
	EXTRACT_BATCH_STATES = (
		(OPEN, 'Open'),
		(IN_PROGRESS, 'In progress'),
		(CLOSED, 'Closed'),
		(STOP, 'Stop')
	)
	status = models.PositiveSmallIntegerField(default = OPEN, choices=EXTRACT_BATCH_STATES)
	
	# return string representing status. For templates
	def get_status(self):
		for state_int, state_name in self.EXTRACT_BATCH_STATES:
			if state_int == self.status:
				return state_name
		raise ValueError(f'No extract batch status {self.status}')
	
	# retain only lysates in layout_element_ids
	# in addition, preserve controls
	def restrict_layout_elements(self, layout_element_ids):
		to_clear = ExtractionBatchLayout.objects.filter(extract_batch=self).exclude(id__in=layout_element_ids).exclude(control_type__isnull=False)
		to_clear.delete()
		
	def create_extracts(self, user):
		# order matters for the creation of controls without prior existing lysates
		layout = ExtractionBatchLayout.objects.filter(extract_batch=self).order_by('column', 'row')
		duplicate_positions_check_db(layout)
		# create extracts
		for layout_element in layout:
			extract = layout_element.create_extract_from_lysate(user)
	
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
								control_set=self.control_set,
								rotated=self.rotated
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
		return library_batch
				
	def rotate(self, user):
		layout_elements = ExtractionBatchLayout.objects.filter(extract_batch=self)
		rotate_plate(layout_elements, user)
		self.rotated = not self.rotated
		self.save(save_user=user)
	
	def extracts_from_spreadsheet(self, spreadsheet, user):
		layout_elements = ExtractionBatchLayout.objects.filter(extract_batch=self)
		headers, data_rows = spreadsheet_headers_and_data_rows(spreadsheet)
			
		for line in data_rows:
			fields = re.split('\t', line)
			
			well_position = get_spreadsheet_value(headers, fields, 'well_position-')
			#print(well_position)
			temp = TimestampedWellPosition()
			temp.set_position(well_position)
			
			layout_element = layout_elements.get(column=temp.column, row=temp.row)
			layout_element.from_spreadsheet_row(headers, fields, user)
	
	def add_lysate(self, lysate_obj, row, column, user):
		# The target well should currently be empty
		try:
			existing = ExtractionBatchLayout.objects.get(extract_batch=self, row=row, column=column)
			# it is acceptable if the lysate is already in this position
			if existing.lysate != lysate_obj:
				raise ValueError(f'{row}{column} in {self.batch_name} is unexpectedly occupied')
		except ExtractionBatchLayout.DoesNotExist:
			lysate_volume_used = (self.protocol.total_lysis_volume * self.protocol.lysate_fraction_extracted)
			layout_element = ExtractionBatchLayout(extract_batch=self, 
								lysate=lysate_obj, lysate_volume_used=lysate_volume_used, 
								row=row, 
								column=column)
			layout_element.save(save_user=user)
		# ExtractionBatchLayout.MultipleObjectsReturned is intentionally not caught
		
	# Extract batches created from lysate batches reuse the controls. 
	# This sets controls for batches starting from this point. 
	# The wetlab calls these Crowds. 
	def set_controls(self, user):
		control_types = EXTRACT_AND_LIBRARY_CONTROLS
		controls = ControlLayout.objects.filter(control_set=self.control_set, control_type__control_type__in=control_types, active=True).order_by('column', 'row')
		
		existing_controls = ExtractionBatchLayout.objects.filter(extract_batch=self, control_type__isnull=False).order_by('column', 'row')
		# examine existing controls for sample numbers and remove existing 
		extract_negative_sample_id, library_negative_sample_id = existing_controls_cleanup(existing_controls, user)
		
		# create new control layout entries
		for control in controls:
			layout_element = ExtractionBatchLayout(extract_batch=self, control_type=control.control_type, row=control.row, column=control.column)
			
			# Skip creating powder samples and lysates for controls because these do not really exist
			layout_element.lysate_volume_used = 0
			layout_element.save(save_user=user)
			
	def crowd_spreadsheet(self, spreadsheet, user):
		self.set_controls(user)
		headers, data_row_fields = spreadsheet_headers_and_data_row_fields(spreadsheet)
		skipped_text = ''

		# Spreadsheet contains either Lysate or Library column to identify lysates
		use_lysate_ids = None
		if 'Lysate' in headers:
			use_lysate_ids = True
		elif 'Library' in headers:
			use_lysate_ids = False
		else:
			raise ValueError("Spreadsheet needs either 'Lysate' or 'Library'")
		
		for line in data_row_fields:
			position_str = get_spreadsheet_value(headers, line, 'Position')
			position = TimestampedWellPosition()
			position.set_position(position_str)
			
			lysate = None
			object_str = None
			if use_lysate_ids:
				object_str = get_spreadsheet_value(headers, line, 'Lysate')
				if object_str.startswith('S'): # ignore controls and nonsamples
					lysate = Lysate.objects.get(lysate_id=object_str)
			else:
				object_str = get_spreadsheet_value(headers, line, 'Library')
				if object_str.startswith('S'): # ignore controls and nonsamples
					library = Library.objects.get(reich_lab_library_id=object_str)
					lysate = library.extract.lysate

			if lysate is not None:
				self.add_lysate(lysate, position.row, position.column, user)
			else:
				skipped_text += f'Crowd spreadsheet skipping: {str(position)} "{object_str}"\n'
				 
		return skipped_text
	
class Extract(Timestamped):
	extract_id = models.CharField(max_length=50, unique=True, db_index=True)
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
	
	def clean(self):
		super(Extract, self).clean()
		if self.sample and self.lysate and self.sample != self.lysate.get_sample():
			raise ValidationError(_('Extract has sample mismatch'))
	
	# ensure this extract has a Reich lab sample number
	def ensure_ids(self):
		self.sample.assign_reich_lab_sample_number()
		
	def num_libraries(self):
		return self.library_set.count()
		
	def get_sample(self):
		if self.sample:
			return self.sample
		elif self.lysate:
			return lysate.get_sample()
		return None
	
# lysate -> extract
class ExtractionBatchLayout(TimestampedWellPosition):
	extract_batch = models.ForeignKey(ExtractionBatch, on_delete=models.CASCADE, null=True) # use a null extract batch to mark lost lysate
	lysate = models.ForeignKey(Lysate, on_delete=models.CASCADE, null=True)
	control_type = models.ForeignKey(ControlType, on_delete=models.PROTECT, null=True)
	lysate_volume_used = models.FloatField(null=True) # for lost only, until we can migrate all values in extracts
	notes = models.TextField(blank=True)
	extract = models.ForeignKey(Extract, on_delete=models.SET_NULL, null=True, help_text='extract created in this well location')
	
	@staticmethod
	def spreadsheet_header(cumulative=False):
		 headers = ['well_position-', 
			'extract_id-',
			'fluidx_barcode-',
			'lysis_volume_extracted',
			'notes',
			#'storage_location',
			]
		 if cumulative:
			 headers += LysateBatchLayout.spreadsheet_header(cumulative)
		 
		 return headers
		
	def to_spreadsheet_row(self, cumulative=False):
		field_list = ExtractionBatchLayout.spreadsheet_header()
		values = []
		values.append(str(self)) # well position
		values.append(get_value(self.extract, 'extract_id'))
		values.append(get_value(self.lysate, 'barcode'))
		values.append(get_value(self.extract, 'lysis_volume_extracted'))
		values.append(get_value(self.extract, 'notes'))
		
		if cumulative:
			additional_values = None
			if self.lysate:
				try:
					lysate_layout_element = LysateBatchLayout.objects.exclude(lysate__lysate_batch__batch_name__startswith='Crowd').get(lysate=self.lysate, lysate__lysate_batch__status=LysateBatch.CLOSED)
					additional_values = lysate_layout_element.to_spreadsheet_row(cumulative)
				except LysateBatchLayout.DoesNotExist:
					pass
				except LysateBatchLayout.MultipleObjectsReturned:
					raise ValueError(f'{self.lysate.lysate_id} has multiple lysate batch layout')
			if additional_values is None:
				additional_values = empty_values(LysateBatchLayout.spreadsheet_header(cumulative))
			values += additional_values
		return values
		
	def from_spreadsheet_row(self, headers, arg_array, user):
		row_extract_id = get_spreadsheet_value(headers, arg_array, 'extract_id-')
		if self.extract:
			extract = self.extract
			if extract.extract_id != row_extract_id:
				raise ValueError(f'extract_id mismatch {extract.extract_id} {row_extract_id}')
			extract.lysis_volume_extracted = float(get_spreadsheet_value(headers, arg_array, 'lysis_volume_extracted'))
			extract.notes = get_spreadsheet_value(headers, arg_array, 'notes')
			extract.save(save_user=user)
			
	def create_extract_from_lysate(self, user):
		lysate = self.lysate
		
		# missing data
		if self.control_type is None and lysate is None:
			return None
		elif self.control_type is not None and self.control_type.control_type == LIBRARY_POSITIVE:
			return None
		elif self.extract is not None: # extract was already created
			return self.extract
		else:
			extract_batch = self.extract_batch
			# library negatives have no lysis volume
			is_library_negative = (self.control_type is not None) and  (self.control_type.control_type == LIBRARY_NEGATIVE)
			lysis_volume_extracted = extract_batch.protocol.total_lysis_volume * extract_batch.protocol.lysate_fraction_extracted if not is_library_negative else 0
			
			# Generating from lysates (either real or control)
			if self.control_type is None or lysate is not None:
				if lysate.powder_sample:
					sample = lysate.powder_sample.sample
				else:
					sample = None
				next_extract_number = lysate.highest_extract() +1
				prior_id = str(lysate.lysate_id)
				
			else: # controls
				sample = None
				next_extract_number = 1 # each control produces its own extract
				# count how many existing controls of this type exist already as extract products to distinctly name each control
				num_existing_extracts = ExtractionBatchLayout.objects.filter(extract_batch=self.extract_batch, control_type=self.control_type, extract__isnull=False).count()
				prior_id = control_name_string(self.extract_batch.batch_name, self.control_type, num_existing_extracts)
			extract_id = f'{prior_id}.E{next_extract_number}'
			print(f'created extract id {extract_id}')
			extract = Extract(extract_id=extract_id,
						reich_lab_extract_number=next_extract_number,
						lysate=lysate,
						sample=sample,
						extract_batch=extract_batch,
						lysis_volume_extracted=lysis_volume_extracted,
						extraction_lab=REICH_LAB)
			extract.save(save_user=user)
			
			self.extract = extract
			self.lysate_volume_used = lysis_volume_extracted
			self.save(save_user=user)
			return extract
			
	def destroy_control(self, user):
		if self.control_type is not None:
			if self.lysate is not None:
				raise NotImplementedError('Not expecting to destroy_control for ExtractionBatch layouts')
			
@receiver(pre_delete, sender=ExtractionBatchLayout, dispatch_uid='extractionbatchlayout_delete_signal')
def delete_dependent_extract(sender, instance, using, **kwargs):
	if instance.extract:
		instance.extract.delete()
	
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
	active = models.BooleanField(default=True)

# Create the library corresponding
# we create library for library positive for record keeping if there is no extract
def create_library_from_extract(layout_element, user):
	library_batch = layout_element.library_batch
	extract = layout_element.extract
	sample = extract.sample if extract else None
	
	if layout_element.library is not None:
		return layout_element.library
	else:
		if extract:
			existing_libraries = extract.num_libraries()
			next_library_number = existing_libraries + 1
			reich_lab_library_id = f'{extract.extract_id}.L{next_library_number}'
		elif layout_element.control_type.control_type == LIBRARY_POSITIVE:
			num_existing = LibraryBatchLayout.objects.filter(library_batch=library_batch, library__isnull=False, control_type__control_type=LIBRARY_POSITIVE).count()
			next_library_number = num_existing + 1
			reich_lab_library_id = f'LP{library_batch.id}.L{next_library_number}'
		# control starting from this step (Mob)
		elif layout_element.control_type.control_type == LIBRARY_NEGATIVE:
			# library negative controls with already created libraries
			num_existing = LibraryBatchLayout.objects.filter(library_batch=library_batch, library__isnull=False, control_type__control_type=LIBRARY_NEGATIVE).count()
			next_library_number = 1
			reich_lab_library_id = f'{control_name_string(library_batch.name, layout_element.control_type, num_existing)}.L{next_library_number}'
		else:
			raise ValueError(f'Unexpected case in creating library, neither extract nor library positive/negative {layout_element.id}')
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
			
		library = Library(sample = sample,
						extract = extract,
						library_batch = library_batch,
						reich_lab_library_id = reich_lab_library_id,
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
	
def validate_odd(value):
	if value % 2 != 1:
		raise ValidationError(
			_('%(value)s is not an odd number'),
			params={'value': value},
		)
	
def validate_even(value):
	if value % 2 != 0:
		raise ValidationError(
			_('%(value)s is not an even number'),
			params={'value': value},
		)

class LibraryBatch(Timestamped):
	name = models.CharField(max_length=150, blank=True, unique=True, help_text='Usually ends with _DS')
	protocol = models.ForeignKey(LibraryProtocol, on_delete=models.PROTECT, null=True)
	technician = models.CharField(max_length=50, blank=True)
	prep_date = models.DateField(null=True)
	prep_note = models.TextField(blank=True)
	prep_robot = models.CharField(max_length=20, blank=True)
	cleanup_robot = models.CharField(max_length=20, blank=True)
	cleanup_person = models.CharField(max_length=50, blank=True)
	cleanup_date =  models.DateField(null=True)
	qpcr_machine = models.CharField(max_length=20, blank=True)
	technician_fk = models.ForeignKey(WetLabStaff, on_delete=models.SET_NULL, null=True)
	control_set = models.ForeignKey(ControlSet, on_delete=models.SET_NULL, null=True)
	rotated = models.BooleanField(default=False, help_text='True for second extract plates that are rotated 180 degrees')
	
	# The offset determines completely the layout of barcodes for the library batch because the wetlab uses a system where the p5 barcodes are placed in the same location for all plates
	# If we need to handle arbitrary layouts, migrate this state into barcodes in the layout objects 
	p7_offset = models.SmallIntegerField(null=True, validators=[MinValueValidator(0), MaxValueValidator(PLATE_WELL_COUNT_HALF-1), validate_even], help_text='Must be even in [0,46]')
	
	OPEN = 0
	IN_PROGRESS = 100
	CLOSED = 200
	STOP = 1000
	LIBRARY_BATCH_STATES = (
		(OPEN, 'Open'),
		(IN_PROGRESS, 'In progress'),
		(CLOSED, 'Closed'),
		(STOP, 'Stop')
	)
	status = models.PositiveSmallIntegerField(default = OPEN, choices=LIBRARY_BATCH_STATES)
	
	# return string representing status. For templates
	def get_status(self):
		for state_int, state_name in self.LIBRARY_BATCH_STATES:
			if state_int == self.status:
				return state_name
		raise ValueError(f'No library batch status {self.status}')
		
	def clean(self):
		if self.status == self.CLOSED and self.prep_date is None:
			raise ValidationError(_('Closed library batch needs prep date'))
	
	def check_p7_offset(self):
		if self.p7_offset is None or self.p7_offset < 0 or self.p7_offset >= PLATE_WELL_COUNT_HALF:
			raise ValueError(f'p7_offset is out of range: {self.p7_offset}')
			
	# convenience 
	def layout_elements(self):
		return LibraryBatchLayout.objects.filter(library_batch=self).order_by('column', 'row', 'library__sample__reich_lab_id')
	
	def create_libraries(self, user):
		self.check_p7_offset()
		layout = self.layout_elements()
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
	def restrict_layout_elements(self, layout_ids, user):
		# remove extracts that are assigned but preserve controls
		to_clear = LibraryBatchLayout.objects.filter(library_batch=self).exclude(id__in=layout_ids).exclude(control_type__isnull=False)
		to_clear.delete()

	# Library batches created from extract batches reuse the controls.
	# This sets controls for batches starting from this point.
	# The wetlab calls these Mobs.
	def set_controls(self, user):
		# extract controls are assigned explicitly, not populated from control set
		control_types = [LIBRARY_NEGATIVE, LIBRARY_POSITIVE]
		controls = ControlLayout.objects.filter(control_set=self.control_set, control_type__control_type__in=control_types, active=True).order_by('column', 'row')

		existing_controls = LibraryBatchLayout.objects.filter(library_batch=self, control_type__control_type__in=control_types).order_by('column', 'row')
		# examine existing controls for sample numbers and remove existing
		extract_negative_sample_id, library_negative_sample_id = existing_controls_cleanup(existing_controls, user)

		# create new control layout entries for library controls
		for control in controls:
			layout_element = LibraryBatchLayout(library_batch=self, control_type=control.control_type, row=control.row, column=control.column)

			layout_element.ul_extract_used = 0
			layout_element.save(save_user=user)
		
	def libraries_from_spreadsheet(self, spreadsheet, user):
		headers, data_rows = spreadsheet_headers_and_data_rows(spreadsheet)
		
		for line in data_rows:
			fields = re.split('\t', line)
			
			well_position = get_spreadsheet_value(headers, fields, 'well_position-')
			temp = TimestampedWellPosition()
			temp.set_position(well_position)
			
			layout_element = self.layout_elements().get(column=temp.column, row=temp.row)
			layout_element.from_spreadsheet_row(headers, fields, user)
		
	
	def create_capture(self, capture_name, other_library_batches, user):
		# fail if a library batch is not ready
		for library_batch in other_library_batches:
			print(library_batch.name)
			if library_batch.status != LibraryBatch.CLOSED:
				raise ValueError(f'{library_batch.name} status is "{library_batch.get_status()}"')
		
		# create capture
		capture_plate = CaptureOrShotgunPlate.objects.create(name=capture_name,
				technician = self.technician,
				technician_fk = self.technician_fk,
			)
		
		# copy from library layout
		other_library_batches_flat = other_library_batches.values_list('id', flat=True)
		to_copy = LibraryBatchLayout.objects.filter(library_batch__in=([self] + [x for x in other_library_batches_flat]), library_batch__status=LibraryBatch.CLOSED).exclude(control_type__control_type=LIBRARY_POSITIVE)
		for x in to_copy:
			copied = CaptureLayout(capture_batch = capture_plate, 
								row = x.row,
								column = x.column,
								library = x.library,
								control_type = x.control_type
								)
			if x.library_batch.rotated:
				copied.rotate() # unrotate
			copied.save(save_user=user)
		# control changes for capture
		# 1. Move library negative in H12 to H9
		# This transformation should be in the control layout but is hard-coded for now
		library_negatives = CaptureLayout.objects.filter(capture_batch=capture_plate, control_type__control_type=LIBRARY_NEGATIVE).order_by('column', 'row')
		#print(f'{len(library_negatives)} library_negatives')
		for to_move in library_negatives.filter(row='H', column=12):
			to_move.row = 'H'
			to_move.column = 9
			to_move.save(save_user=user)
		#print(f'{to_move} {destination}')
		# 2. Replace library positive with PCR negative (G12)
		pcr_negative_position = ControlLayout.objects.get(control_set=self.control_set, control_type__control_type=PCR_NEGATIVE)
		pcr_negative = CaptureLayout(capture_batch=capture_plate,
							   control_type=pcr_negative_position.control_type, row=pcr_negative_position.row, column=pcr_negative_position.column)
		pcr_negative.save(save_user=user)
		# 3. capture positive in H12
		capture_positive_position = ControlLayout.objects.get(control_set=self.control_set, control_type__control_type=CAPTURE_POSITIVE)
		# TODO shotgun does not get a capture positive. Instead it gets a second PCR negative
		# capture positive depends upon library type
		if self.protocol.library_type == 'ds':
			capture_positive_library = Library.objects.get(reich_lab_library_id=CAPTURE_POSITIVE_LIBRARY_NAME_DS)
			capture_positive = CaptureLayout(capture_batch=capture_plate,
								   control_type=capture_positive_position.control_type, row=capture_positive_position.row, column=capture_positive_position.column,
								   library = capture_positive_library)
			capture_positive.save(save_user=user)
		else:
			#raise NotImplementedError(f'Unimplemented capture positive for library type {self.protocol.library_type}')
			pass # TODO wetlab does not have single-stranded capture positive yet
		
	def assign_extract(self, extract, row, column, control_type=None):
		if control_type == None:
		# ensure this extract has a sample number
			extract.ensure_ids()
		try:
			library_batch_layout_element = LibraryBatchLayout.objects.get(library_batch=self,
									extract=extract,
									control_type = control_type,
									row = row,
									column = column)
		except LibraryBatchLayout.DoesNotExist:
			library_batch_layout_element = LibraryBatchLayout(library_batch=self,
									extract=extract,
									control_type = control_type,
									row = row,
									column = column)
			library_batch_layout_element.save()
	
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

REVERSE_COMPLEMENT_MAP = {
	'A': 'T',
	'T': 'A',
	'C': 'G',
	'G': 'C'
	}
def reverse_complement(sequence):
	result = ''
	for char in sequence[::-1]:
		result += REVERSE_COMPLEMENT_MAP[char]
	if len(result) != len(sequence):
		raise ValueError('Length mismatch')
	return result

	
class Barcode(models.Model):
	label = models.CharField(max_length=20, db_index=True)
	sequence = models.CharField(max_length=31, db_index=True, unique=True, validators=[validate_barcode_dna_sequence])
	reich_lab_default = models.BooleanField(default=False)
	
class P5_Index(models.Model):
	label = models.CharField(max_length=10, db_index=True) # cannot be unique because double and single stranded are named with same integers
	label2 = models.CharField(max_length=20, blank=True)
	sequence = models.CharField(max_length=8, db_index=True, unique=True, validators=[validate_index_dna_sequence])
	reich_lab_default = models.BooleanField(default=False)
	
class P7_Index(models.Model):
	label = models.CharField(max_length=10, db_index=True) # cannot be unique because double and single stranded are named with same integers
	label2 = models.CharField(max_length=20, blank=True)
	sequence = models.CharField(max_length=8, db_index=True, unique=True, validators=[validate_index_dna_sequence])
	reich_lab_default = models.BooleanField(default=False)
	
class Library(Timestamped):
	sample = models.ForeignKey(Sample, on_delete=models.PROTECT, null=True)
	extract = models.ForeignKey(Extract, on_delete=models.PROTECT, null=True)
	library_batch = models.ForeignKey(LibraryBatch, on_delete=models.CASCADE, null=True)
	reich_lab_library_id = models.CharField(max_length=50, unique=True, db_index=True)
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
	fluidx_barcode = models.CharField(max_length=12, blank=True, help_text='Physical barcode on FluidX tube')
	
	nanodrop = models.DecimalField(max_digits=5, decimal_places=2, null=True)
	qpcr = models.DecimalField(max_digits=4, decimal_places=2, null=True)
	
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
		if self.sample and self.extract and self.sample != self.extract.get_sample():
			raise ValidationError(_('Library has sample mismatch'))
			
	# barcodes and indices are unique, so we only need to check ids, not DNA sequences
	def barcodes_are_distinct(self, other):
		if self.p5_index and self.p7_index and other.p5_index and other.p7_index:
			return self.p5_index != other.p5_index or self.p7_index != other.p7_index
		elif self.p5_barcode and self.p7_barcode and other.p5_barcode and other.p7_barcode:
			return self.p5_barcode != other.p5_barcode or self.p7_barcode != other.p7_barcode
		else:
			raise ValueError(f'Expecting either 2 indices or 2 barcodes on both libraries {self.reich_lab_library_id} and {other.reich_lab_library_id}')
			
	def get_sample(self):
		if self.sample:
			return self.sample
		elif self.extract:
			return self.extract.get_sample()
		return None
	
# extract -> library
class LibraryBatchLayout(TimestampedWellPosition):
	library_batch = models.ForeignKey(LibraryBatch, on_delete=models.CASCADE, null=True)
	extract = models.ForeignKey(Extract, on_delete=models.CASCADE, null=True)
	control_type = models.ForeignKey(ControlType, on_delete=models.PROTECT, null=True)
	ul_extract_used = models.FloatField(null=True) # populated from library protocol, needs to done after layout elements are created
	notes = models.TextField(blank=True)
	library = models.ForeignKey(Library, on_delete=models.SET_NULL, null=True, help_text='')
	
	@staticmethod
	def spreadsheet_header(cumulative=False):
		headers = ['well_position-',
			'reich_lab_library_id-',
			'p5_barcode',
			'p7_barcode',
			'nanodrop',
			'qpcr',
			'plate_id',
			'fluidx_barcode',
			'notes',
			#'storage_location',
			]
		if cumulative:
			headers += ExtractionBatchLayout.spreadsheet_header(cumulative)
		return headers
		
	def to_spreadsheet_row(self, cumulative=False):
		values = [ str(self),
			get_value(self.library, 'reich_lab_library_id'),
			get_value(self.library, 'p5_barcode', 'label'),
			get_value(self.library, 'p7_barcode', 'label'),
			get_value(self.library, 'nanodrop'),
			get_value(self.library, 'qpcr'),
			get_value(self.library, 'plate_id'),
			get_value(self.library, 'fluidx_barcode'),
			get_value(self.library, 'notes')
			]
		if cumulative:
			additional_values = None
			if self.extract:
				try:
					extraction_layout_element = ExtractionBatchLayout.objects.get(extract=self.extract)
					additional_values = extraction_layout_element.to_spreadsheet_row(cumulative)
				except ExtractionBatchLayout.DoesNotExist:
					pass
			if additional_values is None:
				additional_values = empty_values(ExtractionBatchLayout.spreadsheet_header(cumulative))
			values += additional_values
		return values
		
	def from_spreadsheet_row(self, headers, arg_array, user):
		reich_lab_library_id = get_spreadsheet_value(headers, arg_array, 'reich_lab_library_id-')
		if self.library.reich_lab_library_id != reich_lab_library_id:
			raise ValueError(f'reich_lab_library_id mismatch {self.library.reich_lab_library_id} {reich_lab_library_id}')
		library = self.library
		library.nanodrop = float(arg_array[headers.index('nanodrop')])
		library.qpcr = float(arg_array[headers.index('qpcr')])
		library.plate_id = arg_array[headers.index('plate_id')]
		library.fluidx_barcode = arg_array[headers.index('fluidx_barcode')]
		library.notes = arg_array[headers.index('notes')]
		library.save(save_user=user)
		
@receiver(pre_delete, sender=LibraryBatchLayout, dispatch_uid='librarybatchlayout_delete_signal')
def delete_dependent_library(sender, instance, using, **kwargs):
	if instance.library:
		instance.library.delete()
	
class CaptureProtocol(Timestamped):
	name = models.CharField(max_length=150, unique=True, validators=[validate_no_whitespace, validate_no_underscore])
	start_date = models.DateField(null=True)
	end_date = models.DateField(null=True)
	description = models.TextField(blank=True)
	manuscript_summary = models.TextField(blank=True, help_text='Enrichment method summary for manuscripts')
	protocol_reference = models.TextField(blank=True)
	active = models.BooleanField(default=True)
	
class SequencingPlatform(Timestamped):
	platform = models.CharField(max_length=20)
	note = models.TextField(blank=True)
	location = models.CharField(max_length=50, blank=True, help_text='location of sequencing platform')
	
	active = models.BooleanField(default=True)
	
	def __str__(self):
		return f'{self.platform}'
		
class CaptureOrShotgunPlate(Timestamped):
	name = models.CharField(max_length=50, help_text='Usually ends with _TW or _RW')
	enrichment_type = models.CharField(max_length=20, blank=True)
	protocol = models.ForeignKey(CaptureProtocol, on_delete=models.PROTECT, null=True)
	technician = models.CharField(max_length=10, blank=True)
	technician_fk = models.ForeignKey(WetLabStaff, on_delete=models.SET_NULL, null=True)
	date = models.DateField(null=True)
	robot = models.CharField(max_length=50, blank=True)
	hyb_wash_temps = models.CharField(max_length=50, blank=True)
	reagent_batch = models.PositiveSmallIntegerField(null=True, help_text='Twist batch or bait batch number')
	notes = models.TextField(blank=True)
	
	p5_index_start = models.PositiveSmallIntegerField(null=True, validators=[MinValueValidator(1), MaxValueValidator(47), validate_odd], help_text='Must be odd in [1, 48]')# TODO revisit this for single stranded
	
	needs_sequencing = models.BooleanField(default=True, help_text='True for new plates. False for plates sequenced before website switchover.')
	
	OPEN = 0
	IN_PROGRESS = 100
	CLOSED = 200
	STOP = 1000
	CAPTURE_BATCH_STATES = (
		(OPEN, 'Open'),
		(IN_PROGRESS, 'In Progress'),
		(CLOSED, 'Closed'),
		(STOP, 'Stop')
	)
	status = models.SmallIntegerField(default = OPEN, choices=CAPTURE_BATCH_STATES)
	
	# return string representing status. For templates
	def get_status(self):
		for state_int, state_name in self.CAPTURE_BATCH_STATES:
			if state_int == self.status:
				return state_name
		raise ValueError(f'No capture/raw batch status {self.status}')
	
	def layout_elements(self):
		return CaptureLayout.objects.filter(capture_batch=self).order_by('row', 'column', 'library__sample__reich_lab_id')
	
	def assign_indices(self, user):
		for layout_element in CaptureLayout.objects.filter(capture_batch=self):
			int_position = reverse_plate_location_coordinate(layout_element.row, layout_element.column)
			# indices are only assigned if the library has none
			if layout_element.library is None or (layout_element.library.p5_index is None and layout_element.library.p7_index is None):
				# double-stranded
				p5_int, p7_int = indices_for_location(int_position, self.p5_index_start)
				print(f'indices {p5_int} {p7_int}')
				p5 = P5_Index.objects.get(label=str(p5_int))
				p7 = P7_Index.objects.get(label=str(p7_int))
				layout_element.p5_index = p5
				layout_element.p7_index = p7
				layout_element.save(save_user=user)
			
	def check_library_inputs(self):
		combinations = {}
		for layout_element in CaptureLayout.objects.filter(capture_batch=self):
			# TODO fix barcodes for capture positive and PCR negative
			if layout_element.library:
				s = f'{layout_element.library.p5_barcode}_{layout_element.library.p7_barcode}'
				if s in combinations:
					raise ValueError(f'duplicate barcodes {s} in {self.name}. Existing is {combinations[s]}. Current id is {layout_element.id}.')
				
				if layout_element.library:
					combinations[s] = layout_element.library.reich_lab_library_id
				else:
					combinations[s] = layout_element.control_type.control_type
			
	def restrict_layout_elements(self, layout_ids, user):
		to_clear = CaptureLayout.objects.filter(capture_batch=self).exclude(id__in=layout_ids).exclude(control_type__isnull=False)
		to_clear.delete()
		
	# check libraries in a well position for barcode conflicts
	def well_barcode_check(self):
		layout_element_queryset = CaptureLayout.objects.filter(capture_batch=self)
		barcode_errors = []
		for i in range(PLATE_WELL_COUNT):
			row, column = plate_location(i)
			at_this_location = layout_element_queryset.filter(row=row, column=column)
			for x in at_this_location:
				for y in at_this_location:
					if x.library != y.library and not x.library.barcodes_are_distinct(y.library):
						barcode_errors.append(ValidationError(_('Barcode duplication'), code='barcode_duplicate'))
		if len(barcode_errors) > 0:
			raise ValidationError(barcode_errors)
			
	def clean(self):
		super(CaptureOrShotgunPlate, self).clean()
		if self.status == self.CLOSED:
			if self.date is None:
				raise ValidationError(_('Closed plate needs date'))
			for element in self.layout_elements():
				element.clean()
		self.well_barcode_check()
		
	def from_spreadsheet(self, spreadsheet, user):
		layout_elements = CaptureLayout.objects.filter(capture_batch=self)
		headers, data_rows = spreadsheet_headers_and_data_rows(spreadsheet)
		
		for line in data_rows:
			fields = re.split('\t', line)
			
			well_position = get_spreadsheet_value(headers, fields, 'well_position-')
			temp = TimestampedWellPosition()
			temp.set_position(well_position)
			library_id = get_spreadsheet_value(headers, fields, 'library_id-')
			
			try:
				layout_element = layout_elements.get(column=temp.column, row=temp.row, library__reich_lab_library_id=library_id)
			except (CaptureLayout.DoesNotExist, AttributeError) as e:
				print(f'cannot find layout element {temp.row}{temp.column} {library_id}, trying without library id')
				layout_element = layout_elements.get(column=temp.column, row=temp.row) # PCR Negative, for example
			layout_element.from_spreadsheet_row(headers, fields, user)
	
	def create_sequencing_run(self, sequencing_run_name, user):
		sequencing_run, created = SequencingRun.objects.get_or_create(name=sequencing_run_name)
		if not created:
			raise ValueError(f'SequencingRun {sequencing_run_name} already exists')
		sequencing_run.assign_captures([self.id], user)
		return sequencing_run
		
	def add_library(self, library_str_id, row, column, user):
		control_type = None
		library_to_add = None
		if library_str_id == PCR_NEGATIVE:
			control_type = ControlType.objects.get(control_type=library_str_id)
		elif library_str_id == CAPTURE_POSITIVE or library_str_id == CAPTURE_POSITIVE_LIBRARY_NAME_DS:
			# TODO this assumes double-stranded
			control_type = ControlType.objects.get(control_type=CAPTURE_POSITIVE)
			library_to_add = Library.objects.get(reich_lab_library_id=CAPTURE_POSITIVE_LIBRARY_NAME_DS)
		else:
			library_to_add = Library.objects.get(reich_lab_library_id=library_str_id)
		try:
			layout_element = CaptureLayout.objects.get(capture_batch=self, library=library_to_add, row=row, column=column, control_type=control_type)
		except CaptureLayout.DoesNotExist:
			layout_element = CaptureLayout(capture_batch=self, library=library_to_add, row=row, column=column, control_type=control_type)
			layout_element.save(save_user=user)
		return layout_element
		
	# Shotgun plates do not have capture positive
	def assign_capture_positive_or_pcr_negative(self, is_shotgun=False):
		raise NotImplementedError # needs control layout to toggle between capture positive and PCR negative
	
	def blob_spreadsheet(self, spreadsheet, user):
		headers, data_row_fields = spreadsheet_headers_and_data_row_fields(spreadsheet)
		for line in data_row_fields:
			library_str = get_spreadsheet_value(headers, line, 'Library')
			position_str = get_spreadsheet_value(headers, line, 'Position')
			print(f'{library_str} {position_str}')
			position = TimestampedWellPosition()
			position.set_position(position_str)
			self.add_library(library_str, position.row, position.column, user)

	# single-stranded libraries already have indices assigned
	def requires_p5_index_start(self):
		for layout_element in self.layout_elements():
			if layout_element.control_type == None and get_value(layout_element.library.library_batch.protocol.library_type) == 'ds':
				return True
		return False # single stranded or empty
	
# library -> indices added
class CaptureLayout(TimestampedWellPosition):
	capture_batch = models.ForeignKey(CaptureOrShotgunPlate, on_delete=models.CASCADE) # we don't need to account for lost library
	library = models.ForeignKey(Library, on_delete=models.CASCADE, null=True)
	control_type = models.ForeignKey(ControlType, on_delete=models.PROTECT, null=True)
	notes = models.TextField(blank=True)
	p5_index = models.ForeignKey(P5_Index, on_delete=models.PROTECT, null=True)
	p7_index = models.ForeignKey(P7_Index, on_delete=models.PROTECT, null=True)
	
	nanodrop = models.DecimalField(max_digits=5, decimal_places=2, null=True)
	
	def clean(self):
		super(CaptureLayout, self).clean()
		if self.library:
			has_library_indices = self.library.p5_index is not None and self.library.p7_index is not None
			has_capture_indices = self.p5_index is not None and self.p7_index is not None
			
			exactly_one_index_pair = has_library_indices ^ has_capture_indices
			
			if not exactly_one_index_pair:
				raise ValidationError(_('Captured library should have exactly one pair of indices between capture and library %(p5_index_capture)s %(p7_index_capture)s  %(p5_index_library)s %(p7_index_library)s'), 
							params={'p5_index_capture': self.p5_index,
									'p7_index_capture': self.p7_index,
									'p5_index_library': self.library.p5_index,
									'p5_index_library': self.library.p7_index
					})
		elif self.control_type is None:
			raise ValidationError(_('Should have either library or control'))

	# return the index either from capture, or from library if there
	def _get_index(self, index_str):
		if hasattr(self, index_str):
			index = getattr(self, index_str)
			if index is not None:
				return index
		if hasattr(self.library, index_str):
			return getattr(self.library, index_str)
		return None

	def get_i5(self):
		return self._get_index('p5_index')

	def get_i7(self):
		return self._get_index('p7_index')
						
	@staticmethod
	def spreadsheet_header(no_dashes=False, cumulative=False):
		header = ['well_position-',
			'library_id-',
			'nanodrop',
			'library_batch-',
			'well_position_library_batch-'
			'plate_id-',
			'experiment-',
			'p5_index_label-',
			'p5_index-',
			'p7_index_label-',
			'p7_index-',
			'p5_barcode_label-',
			'p5_barcode-',
			'p7_barcode_label-',
			'p7_barcode-',
			'udg_treatment-',
			'library_type-']
		if cumulative:
			header += LibraryBatchLayout.spreadsheet_header(cumulative)
		if no_dashes:
			return [x.rstrip('-') for x in header]
		else:
			return header
		
	def to_spreadsheet_row(self, cumulative=False):
		# until historical elements are backfilled, need to fill unlinked elements with blanks
		if self.p5_index: # DS
			p5_index_label = self.p5_index.label
			p5_index_sequence = self.p5_index.sequence
		else: # SS or index-only library
			p5_index_label = get_value(self.library, 'p5_index', 'label')
			p5_index_sequence = get_value(self.library, 'p5_index', 'sequence')
			
		if self.p7_index: # DS
			p7_index_label = self.p7_index.label
			p7_index_sequence = self.p7_index.sequence
		else: # SS or index-only library
			p7_index_label = get_value(self.library, 'p7_index', 'label')
			p7_index_sequence = get_value(self.library, 'p7_index', 'sequence')
		
		library_batch = ''
		well_position_library_batch = ''
		p5_barcode_label = ''
		p5_barcode_sequence = ''
		p7_barcode_label = ''
		p7_barcode_sequence = ''
		if self.library:
			identifier = self.library.reich_lab_library_id
			
			p5_barcode_label = get_value(self.library.p5_barcode, 'label')
			p5_barcode_sequence = get_value(self.library.p5_barcode, 'sequence')
			p7_barcode_label = get_value(self.library.p7_barcode, 'label')
			p7_barcode_sequence = get_value(self.library.p7_barcode, 'sequence')
			
			if self.library.library_batch:
				library_batch = self.library.library_batch.name
				library_layout_element = LibraryBatchLayout.objects.filter(library_batch__name=library_batch).get(library=self.library)
				well_position_library_batch = str(library_layout_element)
			else:
				library_batch = ''
				well_position_library_batch = ''
		else:
			identifier = self.control_type.control_type
			
		if self.library:
			udg = self.library.udg_treatment
			library_type = self.library.library_type
		else:
			udg = 'control'
			library_type = 'control'
			
		line = [str(self),
				identifier,
				self.nanodrop,
				library_batch,
				well_position_library_batch,
				get_value(self, 'capture_batch', 'protocol', 'name'),
				p5_index_label,
				p5_index_sequence,
				p7_index_label,
				p7_index_sequence,
				p5_barcode_label,
				p5_barcode_sequence,
				p7_barcode_label,
				p7_barcode_sequence,
				udg,
				library_type,
				]
		if cumulative:
			try:
				library_layout_element = LibraryBatchLayout.objects.filter(library_batch__name=library_batch).get(library=self.library)
				line += library_layout_element.to_spreadsheet_row(cumulative)
			except LibraryBatchLayout.DoesNotExist: # controls with no library
				line += empty_values(LibraryBatchLayout.spreadsheet_header(cumulative))
				
		return line
		
	def from_spreadsheet_row(self, headers, arg_array, user):
		reich_lab_library_id = get_spreadsheet_value(headers, arg_array, 'library_id-')
		if self.library and self.library.reich_lab_library_id != reich_lab_library_id:
			raise ValueError(f'reich_lab_library_id mismatch {self.library.reich_lab_library_id} {reich_lab_library_id}')
		library = self.library
		self.nanodrop = float(arg_array[headers.index('nanodrop')])
		self.save(save_user=user)
		
class SequencingRun(Timestamped):
	name = models.CharField(max_length=50, unique=True, db_index=True)
	technician = models.CharField(max_length=10, blank=True, default='')
	technician_fk = models.ForeignKey(WetLabStaff, on_delete=models.SET_NULL, null=True)
	sequencing = models.ForeignKey(SequencingPlatform, on_delete=models.SET_NULL, null=True)
	notes = models.TextField(blank=True, default='')
	
	read_length = models.CharField(max_length=20, blank=True)
	lanes_estimated = models.FloatField(null=True)
	lanes_sequenced = models.PositiveSmallIntegerField(null=True, help_text='number of lanes for HISeqs or number of runs for Miseq and NextSeq')
	
	date_pooled = models.DateField(null=True, help_text='When date is set, captures can no longer be assigned.')
	date_ready_for_sequencing = models.DateField(null=True)
	date_submitted_for_sequencing = models.DateField(null=True)
	date_data_available = models.DateField(null=True)
	date_analysis_started = models.DateField(null=True)
	date_analysis_complete = models.DateField(null=True)
	date_ready_for_pulldown = models.DateField(null=True)
	date_pulldown_complete = models.DateField(null=True)
	reich_lab_release_version = models.CharField(max_length=20, blank=True)
	
	indexed_libraries = models.ManyToManyField(CaptureLayout, through='SequencedLibrary')
	captures = models.ManyToManyField(CaptureOrShotgunPlate) # for marking whether captures have been sequenced
	
	def assign_captures(self, capture_ids, user):
		# remove captures that are not in list
		for capture in self.captures.all():
			if capture.id not in capture_ids:
				self.captures.remove(capture)
				for element_to_remove in CaptureLayout.objects.filter(capture_batch__id=capture.id):
					try:
						sequenced_library = SequencedLibrary.objects.get(indexed_library=element_to_remove, sequencing_run=self)
						sequenced_library.delete()
					except SequencedLibrary.DoesNotExist:
						pass
		# add captures in list
		for capture_id in capture_ids:
			capture = CaptureOrShotgunPlate.objects.get(id=capture_id)
			self.captures.add(capture)
			for element_to_add in CaptureLayout.objects.filter(capture_batch=capture):
				self.assign_capture_layout_element(element_to_add, user)

	def assign_capture_layout_element(self, capture_layout_element, user, dnu='', notes=''):
		sequenced_library, created = SequencedLibrary.objects.get_or_create(indexed_library=capture_layout_element, sequencing_run=self)
		sequenced_library.do_not_use = dnu
		sequenced_library.notes = notes
		sequenced_library.save(save_user=user)
	
	# only one library type is allowed
	def check_library_type(self):
		for indexed_library in indexed_libraries:
			raise NotImplementedError()
		
	def check_index_barcode_combinations(self):
		combinations = {}
		for sequenced_library in SequencedLibrary.objects.filter(sequencing_run=self):
			layout_element = sequenced_library.indexed_library
			try:
				p5_index = get_value(layout_element, 'get_i5', 'sequence')
				p7_index = get_value(layout_element, 'get_i7', 'sequence')
				p5_barcode = get_value(layout_element, 'library', 'p5_barcode', 'sequence')
				p7_barcode = get_value(layout_element, 'library', 'p7_barcode', 'sequence')
				
				s = f'{p5_index}_{p7_index}_{p5_barcode}_{p7_barcode}'
				this_id = get_value(sequenced_library, 'indexed_library', 'library', 'reich_lab_library_id')
				if s in combinations:
					raise ValueError(f'duplicate index-barcode_combination {s} {combinations[s]} {this_id}')
				combinations[s] = f'{sequenced_library.id} {this_id}'
			except Exception as e:
				library = layout_element.library.reich_lab_library_id if  layout_element.library else ''
				control = layout_element.control_type.control_type if layout_element.control_type else ''
				print(f'error checking {layout_element} {library} {control}')
				raise e
	
	def to_spreadsheet(self, cumulative=False):
		lines = []
		header = SequencedLibrary.spreadsheet_header(cumulative)
		lines.append(header)
		for sequenced_library in SequencedLibrary.objects.filter(sequencing_run=self, ).order_by('indexed_library__column', 'indexed_library__row', 'indexed_library__capture_batch__protocol__name', 'indexed_library__library__sample__reich_lab_id', 'indexed_library__library__reich_lab_library_id'):
			lines.append(sequenced_library.to_spreadsheet_row(cumulative))
		return lines

	# For the analysis pipeline, a sequencing run needs to know the barcodes and indices used to give hints for demultiplexing
	def i5_indices(self):
		indices = [index.sequence for index in P5_Index.objects.filter(reich_lab_default=True)]

		# indices for this sequencing run
		for sequenced_library in SequencedLibrary.objects.filter(sequencing_run=self):
			sequence = get_value(sequenced_library.indexed_library, 'p5_index', 'sequence', default=None)
			if sequence is not None and sequence not in indices:
				indices.append(sequence)
		return indices

	def i7_indices(self):
		indices = [index.sequence for index in P7_Index.objects.filter(reich_lab_default=True)]

		# indices for this sequencing run
		for sequenced_library in SequencedLibrary.objects.filter(sequencing_run=self):
			sequence = get_value(sequenced_library.indexed_library, 'p7_index', 'sequence', default=None)
			if sequence is not None and sequence not in indices:
				indices.append(sequence)
		return indices

	def barcodes(self):
		barcode_sequences = [barcode.sequence for barcode in Barcode.objects.filter(reich_lab_default=True)]

		for sequenced_library in SequencedLibrary.objects.filter(sequencing_run=self):
			p5_barcode_sequence = get_value(sequenced_library.indexed_library, 'library', 'p5_barcode', 'sequence', default=None)
			if p5_barcode_sequence is not None and p5_barcode_sequence not in barcode_sequences:
				barcode_sequences.append(p5_barcode_sequence)

			p7_barcode_sequence = get_value(sequenced_library.indexed_library, 'library', 'p7_barcode', 'sequence', default=None)
			if p7_barcode_sequence is not None and p7_barcode_sequence not in barcode_sequences:
				barcode_sequences.append(p7_barcode_sequence)
		return barcode_sequences


class SequencedLibrary(Timestamped):
	indexed_library = models.ForeignKey(CaptureLayout, on_delete=models.CASCADE)
	sequencing_run = models.ForeignKey(SequencingRun, on_delete=models.CASCADE)

	do_not_use = models.TextField(blank=True)
	notes = models.TextField(blank=True)

	class Meta:
		unique_together = ['indexed_library', 'sequencing_run']

	@staticmethod
	def spreadsheet_header(no_dashes=False, cumulative=False):
		header = CaptureLayout.spreadsheet_header(False, cumulative)
		# add new fields to the right or capture layout fields to preserve
		header += [
			'do_not_use',
			'notes']

		if no_dashes:
			return [x.rstrip('-') for x in header]
		else:
			return header

	def to_spreadsheet_row(self, cumulative=False):
		if self.indexed_library.library:
			library_id = self.indexed_library.library.reich_lab_library_id
		elif self.indexed_library.control_type:
			library_id = self.indexed_library.control_type.control_type
		else:
			raise NotImplementedError()

		line = self.indexed_library.to_spreadsheet_row(cumulative)
		line += [
			self.do_not_use,
			self.notes]
		return line

	def from_spreadsheet_row(self, headers, arg_array, user):
		raise NotImplementedError()
		reich_lab_library_id = get_spreadsheet_value(headers, arg_array, 'library_id-')
		if self.indexed_library.library and self.indexed_library.library.reich_lab_library_id != reich_lab_library_id:
			raise ValueError(f'reich_lab_library_id mismatch {self.indexed_library.library.reich_lab_library_id} {reich_lab_library_id}')
		sequencing_run_name = get_spreadsheet_value(headers, arg_array, 'sequencing_run-')
		if sequencing_run.name != sequencing_run_name:
			raise ValueError(f'sequencing run name mismatch {sequencing_run.name} {sequencing_run_name}')
		self.do_not_use = arg_array[headers.index('do_not_use')]
		self.notes = arg_array[headers.index('notes')]
		self.save(save_user=user)
	
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
	skeletal_element_sent = models.CharField(max_length=50, blank=True)
	sample_grams = models.FloatField(null=True)
	material_returned = models.TextField(blank=True)
	
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
	mt_capture_plate = models.ForeignKey(CaptureOrShotgunPlate, null=True, on_delete=models.SET_NULL, related_name='results_mt')
	mt_seq_run = models.ForeignKey(SequencingRun, null=True, on_delete=models.SET_NULL, related_name='results_mt')
	shotgun_plate = models.ForeignKey(CaptureOrShotgunPlate, null=True, on_delete=models.SET_NULL, related_name='results_shotgun')
	shotgun_seq_run = models.ForeignKey(SequencingRun, null=True, on_delete=models.SET_NULL, related_name='results_shotgun')
	nuclear_capture_plate = models.ForeignKey(CaptureOrShotgunPlate, null=True, on_delete=models.SET_NULL, related_name='results_nuclear')
	nuclear_seq_run = models.ForeignKey(SequencingRun, null=True, on_delete=models.SET_NULL, related_name='results_nuclear')

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

class Project(models.Model):
	name = models.CharField(max_length=100)
	collaborators = models.ManyToManyField(Collaborator)
	samples = models.ManyToManyField(Sample)
	
	analysis_reporting = models.TextField(blank=True)
	notes = models.TextField(blank=True)
