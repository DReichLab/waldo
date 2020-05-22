from django.db import models
from django.utils import timezone
from datetime import date

import re

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
	creation_timestamp = models.DateTimeField(default=timezone.now)
	created_by = models.CharField(max_length=20)
	modification_timestamp = models.DateTimeField(default=timezone.now)
	modified_by = models.CharField(max_length=20)
	
	class Meta:
		abstract = True

class Shipment(Timestamped):
	shipment_name = models.CharField(max_length=30, db_index=True, unique=True)
	arrival_date = models.DateField(null=True)
	arrival_method = models.CharField(max_length=255)
	tracking_number = models.CharField(max_length=30)
	arrival_notes = models.TextField()
	shipment_notes = models.TextField()
	documents_location = models.TextField()
	additional_information_location = models.TextField()
	
class Collaborator(Timestamped):
	first_name = models.CharField(max_length=50, db_index=True)
	last_name = models.CharField(max_length=50, db_index=True)
	title = models.CharField(max_length=65, help_text="Collaborator's professional title", blank=True)
	institution = models.CharField(max_length=100, db_index=True, help_text="Collaborator's associated institution or company")
	department = models.CharField(max_length=110, help_text="Collaborator's department or division", blank=True)
	address_1 = models.CharField(max_length=70)
	address_2 = models.CharField(max_length=50, blank=True)
	address_3 = models.CharField(max_length=50, blank=True)
	city = models.CharField(max_length=50)
	county_region = models.CharField(max_length=50)
	state = models.CharField(max_length=50)
	country = models.CharField(max_length=50, db_index=True)
	postal_code = models.CharField(max_length=20)
	phone_number_office = models.CharField(max_length=30, blank=True)
	phone_number_mobile = models.CharField(max_length=30, blank=True)
	email_1 = models.CharField(max_length=50)
	email_2 = models.CharField(max_length=50, blank=True)
	skype_user_name = models.CharField(max_length=30, blank=True)
	facetime_user_name = models.CharField(max_length=30, blank=True)
	whatsapp_user_name = models.CharField(max_length=30, blank=True)
	twitter = models.CharField(max_length=50, blank=True)
	facebook = models.CharField(max_length=50, blank=True)
	website = models.CharField(max_length=200, blank=True)
	research_gate_academia = models.CharField(max_length=100, blank=True)
	notes = models.TextField(help_text='Additional information about collaborator')
	
	primary_collaborator = models.BooleanField(null=True, db_index=True, help_text='Is this person a Primary Collaborator? This field is used select collaborators for Harvard office of Academic Reasearch Integrity approval')
	ora_approval = models.BooleanField(db_index=True, help_text='Has the Harvard office of Academic Research Integrity cleared this collaborator?')

class WetLabStaff(Timestamped):
	first_name = models.CharField(max_length=30, db_index=True)
	late_name = models.CharField(max_length=30, db_index=True)
	start_date = models.DateField(null=True)
	end_date = models.DateField(null=True)
	title = models.CharField(max_length=50)
	email_1 = models.CharField(max_length=50, blank=True)
	email_2 = models.CharField(max_length=50, blank=True)
	phone_number = models.CharField(max_length=30, blank=True)
	
class SupportStaff(Timestamped):
	first_name = models.CharField(max_length=30, db_index=True)
	late_name = models.CharField(max_length=30, db_index=True)
	start_date = models.DateField(null=True)
	end_date = models.DateField(null=True)
	title = models.CharField(max_length=50)
	email_1 = models.CharField(max_length=50, blank=True)
	email_2 = models.CharField(max_length=50, blank=True)
	phone_number = models.CharField(max_length=30, blank=True)
	
class Return(Timestamped):
	collaborator = models.ForeignKey(Collaborator, on_delete=models.PROTECT)
	return_date = models.DateField(default=date.today)
	return_method = models.CharField(max_length=50)
	tracking_number = models.CharField(max_length=30, blank=True)
	courier_delivery_date = models.DateField(null=True)
	return_notes = models.TextField(blank=True)
	

class Sample(Timestamped):
	reich_lab_id = models.PositiveIntegerField(db_index=True, null=True, help_text=' assigned when a sample is selected from the queue by the wetlab')
	control = models.CharField(max_length=1, blank=True, help_text='Non-empty value indicates this is a control')
	queue_id = models.PositiveIntegerField(db_index=True, unique=True, null=True)
	
	collaborator = models.ForeignKey(Collaborator, on_delete=models.PROTECT, null=True)
	shipment = models.ForeignKey(Shipment, on_delete=models.PROTECT, null=True)
	return_id = models.ForeignKey(Return, on_delete=models.PROTECT, null=True)

	individual_id = models.CharField(max_length=15, blank=True)
	
	skeletal_element = models.CharField(max_length=50, blank=True, help_text='Type of bone sample submitted for aDNA analysis')
	skeletal_code = models.CharField(max_length=150, blank=True, help_text='Sample identification code assigned by the collaborator')
	skeletal_code_renamed = models.TextField(blank=True, help_text='Sample identification code assigned by the Reich Lab')
	sample_date = models.TextField(blank=True, help_text='Age of sample; either a radiocarbon date or a date interval.')
	average_bp_date = models.FloatField(null=True, help_text='Average Before Present date, calculated from average of calibrated date range after conversion to BP dates')
	date_fix_flag = models.CharField(max_length=75, help_text='Flag for any issues with the date information submitted by the collaborator', blank=True)
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
	
	class Meta:
		unique_together = ['reich_lab_id', 'control']
		
class SamplePrepProtocol(Timestamped):
	preparation_method = models.CharField(max_length=50, help_text='Method used to produce bone powder')
	manuscript_summary = models.TextField(help_text='Sampling method summary for manuscripts')
	protocol_reference = models.TextField(blank=True, help_text='Protocol citation')
	notes = models.TextField(blank=True, help_text='Notes about the method used to create bone powder')
	
class PowderBatch(Timestamped):
	name = models.CharField(max_length=50)
	date = models.DateField(null=True)
	technician = models.CharField(max_length=50)
	technician_fk = models.ForeignKey(WetLabStaff, on_delete=models.SET_NULL, null=True)

class PowderSample(Timestamped):
	powder_sample_id = models.CharField(max_length=15, unique=True, null=False, db_index=True)
	sample = models.ForeignKey(Sample, on_delete=models.PROTECT, help_text='Powder was produced from this sample')
	powder_batch = models.ForeignKey(PowderBatch, on_delete=models.PROTECT, help_text='powder belongs to this processing batch', null=True)
	sampling_tech = models.CharField(max_length=15, help_text='Technique used to produce the bone powder')
	sampling_notes = models.TextField(help_text='Notes from technician about sample quality, method used, mg of bone powder produced and storage location', blank=True)
	total_powder_produced_mg = models.FloatField(null=True, help_text='Total miligrams of bone powder produced from the sample')
	storage_location = models.CharField(max_length=50, help_text='Storage location of remaining bone powder')
	sample_prep_lab = models.CharField(max_length=50, blank=True, help_text='Name of lab where bone powder was produced')
	sample_prep_protocol = models.ForeignKey(SamplePrepProtocol, on_delete=models.SET_NULL, null=True)
	
class ExtractionProtocol(Timestamped):
	name = models.CharField(max_length=150)
	start_date = models.DateField(null=True)
	end_date = models.DateField(null=True)
	description = models.TextField(blank=True)
	manual_robotic = models.CharField(max_length=20, blank=True)
	total_lysis_volume = models.FloatField(null=True)
	lysate_fraction_extracted = models.FloatField(null=True)
	final_extract_volume = models.FloatField(null=True)
	binding_buffer = models.CharField(max_length=20, blank=True)
	reference_abbreviation = models.CharField(max_length=150, blank=True)
	protocol_reference = models.TextField(blank=True)
	
class ExtractBatch(Timestamped):
	batch_name = models.CharField(max_length=50)
	protocol = models.ForeignKey(ExtractionProtocol, on_delete=models.PROTECT, null=True)
	technician = models.CharField(max_length=50, blank=True)
	technician_fk = models.ForeignKey(WetLabStaff, on_delete=models.SET_NULL, null=True)
	date = models.DateField(null=True)
	robot = models.CharField(max_length=20, blank=True)
	note = models.TextField(blank=True)

class Lysate(Timestamped):
	lysate_id = models.CharField(max_length=15, unique=True, null=False, db_index=True)
	powder_sample = models.ForeignKey(PowderSample, null=True, on_delete=models.PROTECT)
	powder_used_mg = models.FloatField(null=True, help_text='milligrams of bone powder used in lysis')
	total_volume_produced = models.FloatField(null=True, help_text='Total microliters of lysate produced')
	
	plate_id = models.CharField(max_length=12, blank=True)
	position = models.CharField(max_length=3, blank=True, help_text='Position on plate')
	barcode = models.CharField(max_length=12, blank=True, help_text='Physical barcode on tube')
	notes = models.TextField(blank=True)
	
class Extract(Timestamped):
	extract_id = models.CharField(max_length=20, unique=True, db_index=True)
	lysate_id = models.ForeignKey(Lysate, on_delete=models.PROTECT, null=True)
	extract_batch_id = models.ForeignKey(ExtractBatch, null=True, on_delete=models.PROTECT)
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
	extract_id = models.ForeignKey(Extract, on_delete=models.PROTECT, null=True)
	library_batch_id = models.ForeignKey(LibraryBatch, on_delete=models.PROTECT, null=True)
	reich_lab_library_id = models.CharField(max_length=20, unique=True, db_index=True)
	udg_treatment = models.CharField(max_length=10)
	library_type = models.CharField(max_length=10, blank=True)
	library_prep_lab = models.CharField(max_length=50, blank=True, help_text='Name of lab where library preparation was done')
	ul_extract_used = models.FloatField(null=True)
	# mg_equivalent_powder_used
	alt_category = models.CharField(max_length=20, blank=True)
	notes = models.TextField(blank=True)
	assessment = models.TextField(help_text='Xcontam listed if |Z|>2 standard errors from zero: 0.02-0.05="QUESTIONABLE", >0.05="QUESTIONABLE_CRITICAL" or "FAIL") (mtcontam 97.5th percentile estimates listed if coverage >2: <0.8 is "QUESTIONABLE_CRITICAL", 0.8-0.95 is "QUESTIONABLE", and 0.95-0.98 is recorded but "PASS", gets overriden by ANGSD')
	
class MTCaptureProtocol(Timestamped):
	name = models.CharField(max_length=150)
	start_date = models.DateField()
	end_date = models.DateField()
	description = models.TextField()
	manuscript_summary = models.TextField(blank=True, help_text='Enrichment method summary for manuscripts')
	protocol_reference = models.TextField(blank=True)
	
class NuclearCaptureProtocol(Timestamped):
	name = models.CharField(max_length=150)
	start_date = models.DateField(null=True)
	end_date = models.DateField(null=True)
	description = models.TextField()
	manuscript_summary = models.TextField(blank=True, help_text='Enrichment method summary for manuscripts')
	protocol_reference = models.TextField(blank=True)
	
class SequencingPlatform(Timestamped):
	platform = models.CharField(max_length=20)
	library_type = models.CharField(max_length=20, blank=True)
	read_length = models.CharField(max_length=20)
	note = models.TextField()
	
class MTCapturePlate(Timestamped):
	name = models.CharField(max_length=30)
	protocol = models.ForeignKey(MTCaptureProtocol, on_delete=models.PROTECT, null=True)
	technician = models.CharField(max_length=10, blank=True)
	technician_fk = models.ForeignKey(WetLabStaff, on_delete=models.SET_NULL, null=True)
	date = models.DateField(null=True)
	robot = models.CharField(max_length=20, blank=True)
	
class MTSequencingRun(Timestamped):
	name = models.CharField(max_length=30)
	technician = models.CharField(max_length=10, blank=True)
	technician_fk = models.ForeignKey(WetLabStaff, on_delete=models.SET_NULL, null=True)
	date = models.DateField(null=True)
	sequencing = models.ForeignKey(SequencingPlatform, on_delete=models.SET_NULL, null=True)
	
class ShotgunPool(Timestamped):
	name = models.CharField(max_length=50)
	technician = models.CharField(max_length=10, blank=True)
	technician_fk = models.ForeignKey(WetLabStaff, on_delete=models.SET_NULL, null=True)
	date = models.DateField(null=True)
	
class ShotgunSequencingRun(Timestamped):
	name = models.CharField(max_length=50)
	technician = models.CharField(max_length=10, blank=True)
	technician_fk = models.ForeignKey(WetLabStaff, on_delete=models.SET_NULL, null=True)
	date = models.DateField(null=True)
	sequencing = models.ForeignKey(SequencingPlatform, on_delete=models.SET_NULL, null=True)
	
class NuclearCapturePlate(Timestamped):
	name = models.CharField(max_length=50)
	enrichment_type = models.CharField(max_length=20, blank=True)
	protocol = models.ForeignKey(NuclearCaptureProtocol, on_delete=models.PROTECT, null=True)
	technician = models.CharField(max_length=10, blank=True)
	technician_fk = models.ForeignKey(WetLabStaff, on_delete=models.SET_NULL, null=True)
	date = models.DateField(null=True)
	robot = models.CharField(max_length=50)
	hyb_wash_temps = models.CharField(max_length=50)
	
class NuclearSequencingRun(Timestamped):
	name = models.CharField(max_length=50)
	technician = models.CharField(max_length=10, blank=True)
	technician_fk = models.ForeignKey(WetLabStaff, on_delete=models.SET_NULL, null=True)
	date = models.DateField(null=True)
	sequencing = models.ForeignKey(SequencingPlatform, on_delete=models.SET_NULL, null=True)
	
class ControlsExtract(Timestamped):
	extract_batch = models.ForeignKey(ExtractBatch, on_delete=models.PROTECT)
	ec_count = models.PositiveSmallIntegerField()
	ec_median = models.FloatField()
	ec_max = models.FloatField()
	
class ControlsLibrary(Timestamped):
	library_batch = models.ForeignKey(LibraryBatch, on_delete=models.PROTECT)
	lc_count = models.PositiveSmallIntegerField()
	lc_median = models.FloatField()
	lc_max = models.FloatField()
	
class RadiocarbonShipment(Timestamped):
	ship_id = models.CharField(max_length=20, db_index=True, unique=True)
	ship_date = models.DateField(null=True)
	analysis_lab = models.CharField(max_length=50)
	
class RadiocarbonDatingInvoice(Timestamped):
	invoice_number = models.CharField(max_length=20, db_index=True, unique=True)
	company_name = models.CharField(max_length=50)
	billing_period = models.CharField(max_length=50)
	billing_date = models.DateField()
	item_description = models.TextField()
	number_of_samples = models.PositiveSmallIntegerField(null=True)
	total_charge = models.DecimalField(max_digits=9, decimal_places=2)
	note = models.TextField(blank=True)
	
class RadiocarbonDatedSample(Timestamped):
	sample = models.ForeignKey(Sample, on_delete=models.PROTECT)
	radiocarbon_shipment = models.ForeignKey(RadiocarbonShipment, on_delete=models.PROTECT, null=True)
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
	payment_lab = models.CharField(max_length=50, blank=True)
	invoice = models.ForeignKey(RadiocarbonDatingInvoice, on_delete=models.PROTECT, null=True)
	
class Publication(Timestamped):
	title = models.CharField(max_length=200)
	first_author = models.CharField(max_length=50)
	year = models.PositiveSmallIntegerField()
	journal = models.CharField(max_length=100)
	pages = models.CharField(max_length=30)
	author_list = models.TextField()
	url = models.CharField(max_length=50)
	
class DistributionsShipment(Timestamped):
	collaborator = models.ForeignKey(Collaborator, on_delete=models.PROTECT)
	date = models.DateField(help_text='Distribution shipment date')
	shipment_method = models.CharField(max_length=20, help_text='Shipment method used to send samples: FedEx, USPS, hand carried')
	shipment_tracking_number = models.CharField(max_length=30, help_text='Courier package tracking number')
	shipment_notes = models.TextField(help_text='Any notes associated with the distribution shipment', blank=True)
	delivery_date = models.DateField(help_text='Date distribution shipment was delivered', null=True)
	delivery_notes = models.TextField(help_text='Any notes assoicated with the distribution delivery: person confirming delivery, etc.', blank=True)
	
class DistributionsPowder(Timestamped):
	distribution_shipment = models.ForeignKey(DistributionsShipment, on_delete=models.PROTECT)
	powder_sample = models.ForeignKey(PowderSample, on_delete=models.PROTECT)
	powder_sent_mg = models.FloatField(help_text='Total miligrams of bone powder distributed')
	
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
	assessment = models.TextField(help_text='Xcontam listed if |Z|>2 standard errors from zero: 0.02-0.05="QUESTIONABLE", >0.05="QUESTIONABLE_CRITICAL" or "FAIL") (mtcontam 97.5th percentile estimates listed if coverage >2: <0.8 is "QUESTIONABLE_CRITICAL", 0.8-0.95 is "QUESTIONABLE", and 0.95-0.98 is recorded but "PASS", gets overriden by ANGSD')
