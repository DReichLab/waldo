from django.db import models
from django.utils import timezone
from datetime import date


class Timestamped(models.Model):
	creation_timestamp = models.DateTimeField(default=timezone.now)
	created_by = models.CharField(max_length=20)
	modification_timestamp = models.DateTimeField(default=timezone.now)
	modified_by = models.CharField(max_length=20)
	
	class Meta:
		abstract = True

class Shipment(Timestamped):
	arrival_date = models.DateField()
	number_of_samples_for_analysis = models.PositiveSmallIntegerField()
	total_number_of_samples = models.PositiveSmallIntegerField()
	arrival_method = models.CharField(max_length=255)
	tracking_number = models.CharField(max_length=30)
	arrival_notes = models.TextField()
	shipment_notes = models.TextField()
	storage_location_note = models.TextField()
	special_packaging_location = models.TextField()
	documents_in_package = models.TextField()
	agreement_permits = models.TextField()
	agreement_permit_location = models.TextField()
	supplementary_information = models.TextField()
	supplementary_information_location = models.TextField()
	
class Collaborator(Timestamped):
	first_name = models.CharField(max_length=30, db_index=True)
	last_name = models.CharField(max_length=30, db_index=True)
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
	harvard_ari_approval = models.BooleanField(db_index=True, help_text='Has the Harvard office of Academic Research Integrity cleared this collaborator?')
	
class Return(Timestamped):
	collaborator = models.ForeignKey(Collaborator, on_delete=models.PROTECT)
	return_date = models.DateField(default=date.today)
	return_method = models.CharField(max_length=50)
	tracking_number = models.CharField(max_length=30)
	courier_delivery_date = models.DateField(null=True)
	recipient_delivery_confirmation = models.TextField()
	return_notes = models.TextField()
	

class Sample(Timestamped):
	reich_lab_id = models.PositiveIntegerField(db_index=True)
	
	collaborator = models.ForeignKey(Collaborator, on_delete=models.PROTECT)
	shipment = models.ForeignKey(Shipment, on_delete=models.PROTECT)
	return_id = models.ForeignKey(Return, on_delete=models.PROTECT)

	individual_id = models.CharField(max_length=15)
	
	skeletal_element = models.CharField(max_length=30, help_text='Type of bone sample submitted for aDNA analysis')
	skeletal_code = models.CharField(max_length=150, help_text='Sample identification code assigned by the collaborator')	
	sample_date = models.CharField(max_length=550, help_text='Age of sample; either a radiocarbon date or a date interval.')
	average_bp_date = models.FloatField(help_text='Average Before Present date, calculated from average of calibrated date range after conversion to BP dates')
	date_fix_flag = models.CharField(max_length=75, help_text='Flag for any issues with the date information submitted by the collaborator', blank=True)
	population_label = models.CharField(max_length=100, help_text='Country_Culture_Period of Individual')
	locality = models.CharField(max_length=150, help_text='Location where skeletal remains were found')
	country = models.CharField(max_length=30, help_text='Country where skeletal remains were found')
	latitude = models.CharField(max_length=20, help_text='Latitude where skeletal remains were found') # TODO convert to spatial
	longitude = models.CharField(max_length=20, help_text='Longitude where skeletal remains were found') # TODO
	notes = models.TextField(help_text='Any notes from the collaborator about the individual, sample, site, etc.')
	notes_2 = models.TextField(help_text='Any notes from the collaborator about the individual, sample, site, etc.')
	collaborators = models.TextField(max_length=300, help_text='List of additional collaborators asociated with the sample or reference if sample has been published') # convert to many-to-many field
	morphological_sex = models.CharField(max_length=20, help_text='Sex as determined by skeletal remains') # TODO enumerated? 
	morphological_age = models.CharField(max_length=25, help_text='Age as determined by skeletal remains: adult, child, infant, etc.') # TODO enumerated?
	morphological_age_range = models.CharField(max_length=15, help_text='Age range in years as determined by skeletal remains') # TODO map to interval 
	loan_expiration_date = models.DateField(null=True, help_text='Date by which samples need to be returned to collaborator')
	radiocarbon_dating_status = models.CharField(max_length=120, help_text="David Reich's radiocarbon dating status as noted in his anno file") # TODO enumerate?
	publication = models.CharField(max_length=100, help_text='Publication reference if sample has been published') # TODO many-to-many
	find = models.TextField(help_text='Utilitarian field used to "find" samples by adding data into this field via excel spreadsheet import to create a found set') # TODO eliminate this entirely
	
class PowderBatch(Timestamped):
	name = models.CharField(max_length=50)
	date = models.DateField()
	technician = models.CharField(max_length=50)

class PowderSample(Timestamped):
	sample = models.ForeignKey(Sample, on_delete=models.PROTECT, help_text='Powder was produced from this sample')
	powder_batch = models.ForeignKey(PowderBatch, on_delete=models.PROTECT, help_text='powder belongs to this processing batch')
	sampling_tech = models.CharField(max_length=15, help_text='Technique used to produce the bone powder')
	sampling_notes = models.TextField(help_text='Notes from technician about sample quality, method used, mg of bone powder produced and storage location', blank=True)
	total_powder_produced_mg = models.FloatField(help_text='Total miligrams of bone powder produced from the sample')
	storage_location = models.CharField(max_length=50, help_text='Storage location of remaining bone powder')
	
class Lysate(Timestamped):
	powder_sample = models.ForeignKey(PowderSample, on_delete=models.PROTECT)
	powder_used_mg = models.FloatField(help_text='milligrams of bone powder used in lysis')
	total_volume_produced = models.FloatField(help_text='Total microliters of lysate produced')
	notes = models.TextField(blank=True)
	
class ExtractionProtocol(Timestamped):
	name = models.CharField(max_length=50)
	start_date = models.DateField()
	end_date = models.DateField()
	update_description = models.TextField()
	manual_robotic = models.CharField(max_length=20)
	total_lysis_volume = models.FloatField()
	lysate_fraction_extracted = models.FloatField()
	final_extract_volume_produced = models.FloatField()
	binding_buffer = models.CharField(max_length=20)
	publication_summary = models.TextField()
	
class ExtractBatch(Timestamped):
	batch_name = models.CharField(max_length=50)
	protocol = models.ForeignKey(ExtractionProtocol, on_delete=models.PROTECT)
	technician = models.CharField(max_length=50)
	date = models.DateField()
	robot = models.CharField(max_length=20)
	note = models.TextField()
	
class Extract(Timestamped):
	lysate_id = models.ForeignKey(Lysate, on_delete=models.PROTECT, null=True)
	extract_batch_id = models.ForeignKey(ExtractBatch, on_delete=models.PROTECT)
	lysis_volume_extracted = models.FloatField()
	notes = models.TextField(blank=True)
	
class Library(Timestamped):
	udg_treatment = models.CharField(max_length=10)
	ul_extract_used = models.FloatField()
	# mg_equivalent_powder_used
	alt_category = models.TextField()
	notes = models.TextField()
	find = models.CharField(max_length=50)

class ControlsExtract(Timestamped):
	ec_count = models.PositiveSmallIntegerField()
	ec_median = models.FloatField()
	ec_max = models.FloatField()
	
class ControlsLibrary(Timestamped):
	lc_count = models.PositiveSmallIntegerField()
	lc_median = models.FloatField()
	lc_max = models.FloatField()
	
class LibraryProtocol(Timestamped):
	name = models.CharField(max_length=50)
	start_date = models.DateField()
	end_date = models.DateField()
	update_description = models.TextField()
	publication_summary = models.TextField()
	manual_robotic = models.CharField(max_length=20)
	volumne_extract_used_standard = models.FloatField()

class LibraryBatch(Timestamped):
	name = models.CharField(max_length=50)
	protocol = models.ForeignKey(LibraryProtocol, on_delete=models.PROTECT)
	technician = models.CharField(max_length=50)
	prep_date = models.DateField()
	prep_note = models.TextField()
	prep_robot = models.CharField(max_length=20)
	
class MTCaptureProtocol(Timestamped):
	name = models.CharField(max_length=50)
	start_date = models.DateField()
	end_date = models.DateField()
	update_description = models.TextField()
	publication_summary = models.TextField()
	
class NuclearCaptureProtocol(Timestamped):
	name = models.CharField(max_length=50)
	start_date = models.DateField()
	end_date = models.DateField()
	update_description = models.TextField()
	publication_summary = models.TextField()
	
class MTCapturePlate(Timestamped):
	name = models.CharField(max_length=30)
	protocol = models.ForeignKey(MTCaptureProtocol, on_delete=models.PROTECT, null=True)
	technician = models.CharField(max_length=50)
	date = models.DateField()
	robot = models.CharField(max_length=20)
	
class MTSequencingRun(Timestamped):
	name = models.CharField(max_length=30)
	technician = models.CharField(max_length=50)
	date = models.DateField()
	
class ShotgunPool(Timestamped):
	name = models.CharField(max_length=50)
	technician = models.CharField(max_length=50)
	date = models.DateField()
	
class ShotgunSequencingRun(Timestamped):
	name = models.CharField(max_length=50)
	technician = models.CharField(max_length=50)
	date = models.DateField()
	
class NuclearCapturePlate(Timestamped):
	name = models.CharField(max_length=50)
	enrichment_type = models.CharField(max_length=50)
	protocol = models.ForeignKey(NuclearCaptureProtocol, on_delete=models.PROTECT, null=True)
	technician = models.CharField(max_length=50)
	date = models.DateField()
	robot = models.CharField(max_length=50)
	hyb_wash_temps = models.CharField(max_length=50)
	
class NuclearSequencingRun(Timestamped):
	name = models.CharField(max_length=50)
	technician = models.CharField(max_length=50)
	date = models.DateField()
	
class RadiocarbonShipment(Timestamped):
	ship_date = models.DateField()
	analysis_lab = models.CharField(max_length=50)
	
class RadiocarbonDatingInvoice(Timestamped):
	company_name = models.CharField(max_length=50)
	billing_period = models.CharField(max_length=50)
	billing_date = models.DateField()
	item_description = models.TextField()
	number_of_samples = models.PositiveSmallIntegerField()
	total_charge = models.DecimalField(max_digits=9, decimal_places=2)
	
class RadiocarbonDatedSample(Timestamped):
	sample = models.ForeignKey(Sample, on_delete=models.PROTECT)
	radiocarbon_shipment = models.ForeignKey(RadiocarbonShipment, on_delete=models.PROTECT)
	notes = models.TextField()
	material = models.CharField(max_length=50)
	fraction_modern = models.FloatField()
	fraction_modern_plus_minus = models.FloatField()
	d14c_per_mille = models.FloatField()
	d14c_per_mille_plus_minus = models.FloatField()
	age_14c_bp = models.FloatField()
	age_14c_bp_plus_minus = models.FloatField()
	delta13c_per_mille = models.FloatField()
	delta15n_per_mille = models.FloatField()
	percent_carbon = models.FloatField()
	percent_nitrogen = models.FloatField()
	carbon_to_nitrogen_ratio = models.FloatField()
	run_date = models.DateField()
	lab_code = models.CharField(max_length=50)
	payment_lab = models.CharField(max_length=50)
	invoice = models.ForeignKey(RadiocarbonDatingInvoice, on_delete=models.PROTECT)
	find = models.CharField(max_length=10)
	
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
	shipment_notes = models.TextField(help_text='Any notes associated with the distribution shipment')
	delivery_date = models.DateField(help_text='Date distribution shipment was delivered')
	delivery_notes = models.TextField(help_text='Any notes assoicated with the distribution delivery: person confirming delivery, etc.')
	
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
