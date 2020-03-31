from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from datetime import datetime, timedelta, timezone, date
import pandas
from pandas import ExcelFile
from samples.models import Shipment, Collaborator, Return, Sample, PowderBatch, PowderSample, Lysate, ExtractionProtocol, ExtractBatch, Extract, Library, ControlsExtract, ControlsLibrary, LibraryProtocol, LibraryBatch, MTCaptureProtocol, NuclearCaptureProtocol, MTCapturePlate, MTSequencingRun, ShotgunPool, ShotgunSequencingRun, NuclearCapturePlate, NuclearSequencingRun, RadiocarbonShipment, RadiocarbonDatingInvoice, RadiocarbonDatedSample, DistributionsShipment, DistributionsLysate, parse_sample_string, Results
from sequencing_run.models import MTAnalysis, SpikeAnalysis, ShotgunAnalysis, NuclearAnalysis
import sys
from decimal import *

from sequencing_run.assemble_libraries import flowcells_for_names, generate_bam_lists, generate_bam_list_with_sample_data, index_barcode_match

class Command(BaseCommand):
	help = 'Import table from Rebecca'
	
	def add_arguments(self, parser):
		parser.add_argument("table_type")
		parser.add_argument("spreadsheet", help="Excel spreadsheet containing")
		
	def handle(self, *args, **options):
		process_row_map = {
			'collaborator': self.collaborator,
			'shipment': self.shipment,
			'return' : self.return_shipment,
			'sample' : self.sample,
			'powder_batch': self.powder_batch,
			'powder_sample': self.powder_sample,
			'lysate': self.lysate,
			'extraction_protocol': self.extraction_protocol,
			'extract_batch': self.extract_batch,
			'extract': self.extract,
			'library': self.library,
			'controls_extract': self.controls_extract,
			'controls_library': self.controls_library,
			'library_protocol': self.library_protocol,
			'library_batch': self.library_batch,
			'nuclear_capture_protocol': self.nuclear_capture_protocol,
			'mt_capture_plate': self.mt_capture_plate,
			'mt_sequencing_run': self.mt_sequencing_run,
			'shotgun_pool': self.shotgun_pool,
			'shotgun_sequencing_run': self.shotgun_sequencing_run,
			'nuclear_capture_plate': self.nuclear_capture_plate,
			'nuclear_sequencing_run': self.nuclear_sequencing_run,
			'radiocarbon_shipment': self.radiocarbon_shipment,
			'radiocarbon_dating_invoice': self.radiocarbon_dating_invoice,
			'radiocarbon_dated_sample': self.radiocarbon_dated_sample,
			'distributions_shipment': self.distributions_shipment,
			'distributions_lysate': self.distributions_lysate,
			'results': self.results
		}
		
		spreadsheet = options['spreadsheet']
		process_row = process_row_map[options['table_type'].lower()]
		
		df = pandas.read_excel(spreadsheet)
		df = df.fillna('') # replace NaN with empty string

		for index, row in df.iterrows():
			try:
				process_row(row)
			except Exception as e:
				print(row, file=sys.stderr)
				raise e
		
		self.stderr.write(options['table_type'])
			
	def timestring_todb(self, datetime_string):
		eastern_daylight_timedelta = timedelta(hours=-4)
		local_datetime = datetime.strptime(datetime_string, "%m/%d/%Y %H:%M:%S")
		utc_datetime_naive = local_datetime - eastern_daylight_timedelta
		utc_datetime_aware = utc_datetime_naive.replace(tzinfo=timezone.utc)
		return utc_datetime_aware
	
	def pandas_timestamp_todb(self, pandas_timestamp):
		eastern_daylight_timedelta = timedelta(hours=-4)
		try:
			local_datetime = pandas_timestamp.to_pydatetime()
			utc_datetime_naive = local_datetime - eastern_daylight_timedelta
			utc_datetime_aware = utc_datetime_naive.replace(tzinfo=timezone.utc)
			return utc_datetime_aware
		except AttributeError:
			return None
		
	def pandas_timestamp_todb_date(self, pandas_timestamp):
		try:
			return self.pandas_timestamp_todb(pandas_timestamp).date()
		except AttributeError:
			return None
	
	def int_or_null(self, int_string):
		try:
			return int(int_string)
		except ValueError:
			return None
	
	def float_or_null(self, float_string):
		try:
			return float(float_string)
		except ValueError:
			return None
	
	def shipment(self, row):		
		Shipment.objects.create(
			text_id = row['Shipment_ID_pk'],
			arrival_date = self.pandas_timestamp_todb_date(row['Arrival_Date']),
			arrival_method = row['Arrival_Method'],
			tracking_number = row['Tracking_Number'],
			arrival_notes = row['Arrival_Notes'],
			shipment_notes = row['Shipment_Notes'],
			documents_location = row['Agreement_Permit_Location'],
			additional_information_location = row['Supplementary_Information_Location'],
			creation_timestamp = self.pandas_timestamp_todb(row['CreationTimestamp']),
			created_by = row['CreatedBy'],
			modification_timestamp = self.pandas_timestamp_todb(row['ModificationTimestamp']),
			modified_by = row['ModifiedBy']
			)

	def collaborator(self, row):
		Collaborator.objects.create(
			id=int(row['Collaborator_ID_pk'][1:]),
			first_name = row['First_Name'],
			last_name = row['Last_Name'],
			title = row['Title'],
			institution = row['Institution'],
			department = row['Department'],
			address_1 = row['Address_1'],
			address_2 = row['Address_2'],
			address_3 = row['Address_3'],
			city = row['City'],
			county_region = row['County_Region'],
			state = row['State'],
			country = row['Country'],
			postal_code = row['Postal_Code'],
			phone_number_office = row['Phone_Number_Office'],
			phone_number_mobile = row['Phone_Number_Mobile'],
			email_1 = row['Email_1'],
			email_2 = row['Email_2'],
			skype_user_name = row['Skype_UserName'],
			facetime_user_name = row['FaceTime_UserName'],
			whatsapp_user_name = row['WhatsApp_UserName'],
			twitter = row['Twitter'],
			facebook = row['Facebook'],
			website = row['Website'],
			research_gate_academia = row['ResearchGate_Academia'],
			notes = row['Collaborator_Notes'],
			primary_collaborator = bool(row.get('Primary_Collaborator', False)),
			ora_approval = bool(row.get('Harvard_ARI_Approval', False)),
			creation_timestamp = self.pandas_timestamp_todb(row['CreationTimestamp']),
			created_by = row['CreatedBy'],
			modification_timestamp = self.pandas_timestamp_todb(row['ModificationTimestamp']),
			modified_by = row['ModifiedBy']
			)
		
	def return_shipment(self, row):
		Return.objects.create(
			id = int(row['Return_ID_pk'][1:]),
			collaborator = Collaborator.objects.get(id=int(row['Collaborator_ID_fk'][1:])),
			return_date = self.pandas_timestamp_todb_date(row['Return_Date']),
			return_method = row['Return_Method'],
			tracking_number = row['Tracking_Number'],
			courier_delivery_date = self.pandas_timestamp_todb_date(row['Courier_Delivery_Date']),
			return_notes = row['Return_Notes'],

			creation_timestamp = self.pandas_timestamp_todb(row['CreationTimestamp']),
			created_by = row['CreatedBy'],
			modification_timestamp = self.pandas_timestamp_todb(row['ModificationTimestamp']),
			modified_by = row['ModifiedBy']
		)

	def sample(self, row):
		# sample identifier must parse
		try:
			reich_lab_id_number, control = parse_sample_string(row['Sample_ID_pk'])
		except ValueError:
			reich_lab_id_number = None
			control = ''
		# find foreign keys for nullable fields
		try:
			collaborator_foreign = Collaborator.objects.get(id=int(row['Collaborator_ID_fk'][1:]))
		except (Collaborator.DoesNotExist, ValueError) as e:
			collaborator_foreign = None
		try:
			shipment_foreign = Shipment.objects.get(text_id=row['Shipment_ID_fk'])
		except Shipment.DoesNotExist as e:
			shipment_foreign = None
		try:
			return_foreign = Return.objects.get(id=int(row['Return_ID_fk'][1:]))
		except (Return.DoesNotExist, ValueError) as e:
			return_foreign = None
			
		# create sample object
		Sample.objects.create(
			id = int(row['SampleRecordID'][2:]),
			reich_lab_id = reich_lab_id_number,
			control = control,
			queue_id = self.int_or_null(row['Queue_ID']),
			collaborator = collaborator_foreign,
			shipment = shipment_foreign,
			return_id = return_foreign,
			#Sample_Publications_fk
			individual_id = row['Individual_ID'],
			skeletal_element = row['Skeletal_Element'],
			skeletal_code = row['Skeletal_Code'],
			skeletal_code_renamed = row['Skeletal_Code_Renamed'],
			sample_date = row['Sample_Date'],
			average_bp_date = self.float_or_null(row['Average_BP_Date']),
			date_fix_flag = row['Date_Fix_Flag'],
			group_label = row['Population_Label'],
			locality = row['Locality'],
			country = row['Country'],
			latitude = row['Latitude'],
			longitude = row['Longitude'],
			notes = row['Notes'],
			notes_2 = row['Notes_2'],
			collaborators = row['Associated_Collaborators'],
			morphological_sex = row['Morphological_Sex'],
			morphological_age = row['Morphological_Age'],
			morphological_age_range = row['Morphological_Age_Range'],
			loan_expiration_date = self.pandas_timestamp_todb_date(row['Loan_Expiration_Date']),
			dating_status = row['Radiocarbon_Dating_Status'],
			
			creation_timestamp = self.pandas_timestamp_todb(row['CreationTimestamp']),
			created_by = row['CreatedBy'],
			modification_timestamp = self.pandas_timestamp_todb(row['ModificationTimestamp']),
			modified_by = row['ModifiedBy']
		)
		
	def powder_batch(self, row):
		PowderBatch.objects.create(
			id = int(row['Powder_Batch_pk'][2:]),
			name = row['Powder_Batch_Name'],
			date = self.pandas_timestamp_todb_date(row['Powder_Batch_Date']),
			technician = row['Powder_Batch_Technician'],
			
			creation_timestamp = self.pandas_timestamp_todb(row['CreationTimestamp']),
			created_by = row['CreatedBy'],
			modification_timestamp = self.pandas_timestamp_todb(row['ModificationTimestamp']),
			modified_by = row['ModifiedBy']
		)
	
	def powder_sample(self, row):
		# sample must parse
		reich_lab_id_number, control = parse_sample_string(row['Sample_ID_fk'])
		# find foreign keys for nullable fields
		try:
			powder_batch_foreign = PowderBatch.objects.get(id=int(row['Powder_Batch_ID_fk'][2:]))
		except (PowderBatch.DoesNotExist, ValueError) as e:
			powder_batch_foreign = None
		
		PowderSample.objects.create(
			powder_sample_id = row['Powder_Sample_ID_pk'],
			sample = Sample.objects.get(reich_lab_id=reich_lab_id_number, control=control),
			powder_batch = powder_batch_foreign,
			sampling_tech = row['Sampling_Tech'],
			sampling_notes = row['Sampling_Notes'],
			total_powder_produced_mg =  self.float_or_null(row['Total_mg_Powder_Produced']),
			storage_location = row['Storage_Location'],
			
			creation_timestamp = self.pandas_timestamp_todb(row['CreationTimestamp']),
			created_by = row['CreatedBy'],
			modification_timestamp = self.pandas_timestamp_todb(row['ModificationTimestamp']),
			modified_by = row['ModifiedBy']
		)
		
	def lysate(self, row):
		try:
			powder_sample_id_foreign = PowderSample.objects.get(powder_sample_id=row['Powder_Sample_ID_fk'])
		except (PowderSample.DoesNotExist, ValueError) as e:
			powder_sample_id_foreign = None
		Lysate.objects.create(
			lysate_id = row['Lysate_ID_pk'],
			powder_sample = powder_sample_id_foreign,
			powder_used_mg = self.float_or_null(row['mg_Powder_Used']),
			total_volume_produced = self.float_or_null(row['Lysate_Total_Volume_Produced']),
			plate_id= row['PlateID'],
			position = row['Position'],
			barcode = row['Barcode'],
			notes = row['Lysis_Note'],
			
			creation_timestamp = self.pandas_timestamp_todb(row['CreationTimestamp']),
			created_by = row['CreatedBy'],
			modification_timestamp = self.pandas_timestamp_todb(row['ModificationTimestamp']),
			modified_by = row['ModifiedBy']
		)
		
	def extraction_protocol(self, row):
		ExtractionProtocol.objects.create(
			id = int(row['Extraction_Protocol_ID_pk'][2:]),
			name = row['Extraction_Protocol_Name'],
			start_date = self.pandas_timestamp_todb_date(row['Extraction_Protocol_Start_Date']),
			end_date = self.pandas_timestamp_todb_date(row['Extraction_Protocol_End_Date']),
			update_description = row['Extraction_Protocol_Update_Description'],
			manual_robotic = row['Manual_Robotic'],
			total_lysis_volume = self.float_or_null(row['Total_Lysis_Volume']),
			lysate_fraction_extracted = self.float_or_null(row['Lysaste_Fraction_Extracted']),
			final_extract_volume = self.float_or_null(row['Final_Extract_Volume_Produced']),
			binding_buffer = row['Binding_Buffer'],
			reference_abbreviation = row['Ext_Method_Ref_Abbrev'],
			publication_summary = row['Extraction_Protocol_Pub_Summary'],
			
			creation_timestamp = self.pandas_timestamp_todb(row['CreationTimestamp']),
			created_by = row['CreatedBy'],
			modification_timestamp = self.pandas_timestamp_todb(row['ModificationTimestamp']),
			modified_by = row['ModifiedBy']
		)

	def extract_batch(self, row):
		try:
			extraction_protocol_foreign = ExtractionProtocol.objects.get(id=int(row['Extraction_Protocol_ID_fk'][2:]))
		except (ExtractionProtocol.DoesNotExist, ValueError) as e:
			extraction_protocol_foreign = None
		
		ExtractBatch.objects.create(
			id = int(row['Extract_Batch_pk'][2:]),
			batch_name = row['Extract_Batch_Name'],
			protocol = extraction_protocol_foreign,
			technician = row['Extract_Technician'],
			date = self.pandas_timestamp_todb_date(row['Extraction_Date']),
			robot = row['Extraction_Robot'],
			note = row['Extraction_Note'],

			creation_timestamp = self.pandas_timestamp_todb(row['CreationTimestamp']),
			created_by = row['CreatedBy'],
			modification_timestamp = self.pandas_timestamp_todb(row['ModificationTimestamp']),
			modified_by = row['ModifiedBy']
		)
		
	def extract(self, row):
		try:
			extract_batch_id_foreign = ExtractBatch.objects.get(id=int(row['Extract_Batch_ID_fk'][2:]))
		except (ExtractBatch.DoesNotExist, ValueError) as e:
			extract_batch_id_foreign = None
		try:
			lysate_id_foreign = Lysate.objects.get(lysate_id=row['Lysate_ID_fk'])
		except (Lysate.DoesNotExist, ValueError) as e:
			lysate_id_foreign = None
			
		Extract.objects.create(
			extract_id = row['Extract_ID_pk'],
			lysate_id = lysate_id_foreign,
			extract_batch_id = extract_batch_id_foreign,
			lysis_volume_extracted = self.float_or_null(row['Lysis_Volume_Extracted']),
			#extract_volume_remaining = self.float_or_null(row['Extract_Volume_Remaining']),
			notes = row['Extraction_Note'],
			storage_location = row['Extract_Storage_Location'],
			
			creation_timestamp = self.pandas_timestamp_todb(row['CreationTimestamp']),
			created_by = row['CreatedBy'],
			modification_timestamp = self.pandas_timestamp_todb(row['ModificationTimestamp']),
			modified_by = row['ModifiedBy']
		)
		
	def library(self, row):
		Library.objects.create(
			reich_lab_library_id = row['Library_ID_pk'],
			udg_treatment = row['UDG_Treatment'],
			ul_extract_used = self.float_or_null(row['uL_Extract_Used']),
			alt_category = row['Alt_Category'], 
			notes = row['Library_Notes'],
			
			creation_timestamp = self.pandas_timestamp_todb(row['CreationTimestamp']),
			created_by = row['CreatedBy'],
			modification_timestamp = self.pandas_timestamp_todb(row['ModificationTimestamp']),
			modified_by = row['ModifiedBy']
		)

	def controls_extract(self, row):
		try:
			nuclear_sequencing_run_foreign = NuclearSequencingRun.objects.get(id=int(row['Nuclear_Sequencing_Run_fk'][3:]))
		except (NuclearSequencingRun.DoesNotExist, ValueError) as e:
			nuclear_sequencing_run_foreign = None
		
		ControlsExtract.objects.create(
			id = int(row['EC_Group_ID_pk'][2:]),
			extract_batch = ExtractBatch.objects.get(id=int(row['Extract_Batch_fk'][2:])),
			nuclear_sequencing_run = nuclear_sequencing_run_foreign,
			ec_count = int(row['EC_Count']),
			ec_median = float(row['EC_Median']),
			ec_max = float(row['EC_Max']),
			
			creation_timestamp = self.pandas_timestamp_todb(row['CreationTimestamp']),
			created_by = row['CreatedBy'],
			modification_timestamp = self.pandas_timestamp_todb(row['ModificationTimestamp']),
			modified_by = row['ModifiedBy']
		)
	
	def controls_library(self, row):
		try:
			nuclear_sequencing_run_foreign = NuclearSequencingRun.objects.get(id=int(row['Nuclear_Sequencing_Run_fk'][3:]))
		except (NuclearSequencingRun.DoesNotExist, ValueError) as e:
			nuclear_sequencing_run_foreign = None
		
		ControlsLibrary.objects.create(
			id = int(row['LC_Group_ID_pk'][2:]),
			library_batch = LibraryBatch.objects.get(id=int(row['Library_Batch_fk'][2:])), 
			nuclear_sequencing_run = nuclear_sequencing_run_foreign,
			lc_count = int(row['LC_Count']),
			lc_median = float(row['LC_Median']),
			lc_max = float(row['LC_Max']),
			
			creation_timestamp = self.pandas_timestamp_todb(row['CreationTimestamp']),
			created_by = row['CreatedBy'],
			modification_timestamp = self.pandas_timestamp_todb(row['ModificationTimestamp']),
			modified_by = row['ModifiedBy']
		)
		
	def library_protocol(self, row):
		LibraryProtocol.objects.create(
			id = int(row['Library_Prep_Protocol_ID_pk'][3:]),
			name = row['Library_Prep_Protocol_Name'],
			start_date = self.pandas_timestamp_todb_date(row['Library_Prep_Protocol_Start_Date']),
			end_date = self.pandas_timestamp_todb_date(row['Library_Prep_Protocol_End_Date']),
			update_description = row['Library_Prep_Protocol_Update_Description'],
			library_method_reference_abbreviation = row['Lib_Method_Ref_Abbrev'],
			publication_summary = row['Library_Prep_Protocol_Pub_Summary'],
			manual_robotic = row['Manual_Robotic'],
			volume_extract_used_standard = self.float_or_null(row['Volume_Extract_Used_Standard']),
			
			creation_timestamp = self.pandas_timestamp_todb(row['CreationTimestamp']),
			created_by = row['CreatedBy'],
			modification_timestamp = self.pandas_timestamp_todb(row['ModificationTimestamp']),
			modified_by = row['ModifiedBy']
		)
		
	def library_batch(self, row):
		try:
			library_protocol_foreign = LibraryProtocol.objects.get(id=int(row['Library_Prep_Protocol_ID_fk'][3:]))
		except (LibraryProtocol.DoesNotExist, ValueError) as e:
			library_protocol_foreign = None
		
		LibraryBatch.objects.create(
			id = int(row['Library_Batch_pk'][2:]),
			name = row['Library_Batch_Name'],
			protocol = library_protocol_foreign,
			technician = row['Library_Technician'],
			prep_date = self.pandas_timestamp_todb_date(row['Library_Prep_Date']),
			prep_note = row['Library_Prep_Note'],
			prep_robot = row['Library_Prep_Robot'],
			
			creation_timestamp = self.pandas_timestamp_todb(row['CreationTimestamp']),
			created_by = row['CreatedBy'],
			modification_timestamp = self.pandas_timestamp_todb(row['ModificationTimestamp']),
			modified_by = row['ModifiedBy']
		)
	
	# def mt_capture_protocol(self, row): unused for now
		
	def nuclear_capture_protocol(self, row):
		NuclearCaptureProtocol.objects.create(
			id = int(row['Nuclear_Capture_Protocol_ID_pk'][3:]),
			name = row['Nuclear_Capture_Protocol_Name'], 
			start_date = self.pandas_timestamp_todb_date(row['Nuclear_Capture_Protocol_Start_Date']), 
			end_date = self.pandas_timestamp_todb_date(row['Nuclear_Capture_Protocol_End_Date']), 
			update_description = row['Nuclear_Capture_Protocol_Update_Description'],
			publication_summary = ['Nuclear_Capture_Protocol_Pub_Summary'],

			creation_timestamp = self.pandas_timestamp_todb(row['CreationTimestamp']),
			created_by = row['CreatedBy'],
			modification_timestamp = self.pandas_timestamp_todb(row['ModificationTimestamp']),
			modified_by = row['ModifiedBy']
		)
		
	def mt_capture_plate(self, row):
		try:
			mt_protocol_foreign = MTCaptureProtocol.objects.get(int(row['MT_Capture_Protocol_ID_fk']))
		except (MTCaptureProtocol.DoesNotExist, ValueError) as e:
			mt_protocol_foreign = None
		
		MTCapturePlate.objects.create(
			id = int(row['MT_Capture_Plate_pk'][4:]),
			name = row['MT_Capture_Plate_Name'],
			protocol = mt_protocol_foreign,
			technician = row['MT_Capture_Technician'],
			date = self.pandas_timestamp_todb_date(row['MT_Capture_Date']), 
			robot = row['MT_Capture_Robot'],
			
			creation_timestamp = self.pandas_timestamp_todb(row['CreationTimestamp']),
			created_by = row['CreatedBy'],
			modification_timestamp = self.pandas_timestamp_todb(row['ModificationTimestamp']),
			modified_by = row['ModifiedBy']
		)

	def mt_sequencing_run(self, row):
		MTSequencingRun.objects.create(
			id = int(row['MT_Seq_Run_pk'][4:]),
			name = row['MT_Seq_Run_Name'],
			technician = row['MT_Seq_Technician'],
			date = self.pandas_timestamp_todb_date(row['MT_Seq_Date']),
			
			creation_timestamp = self.pandas_timestamp_todb(row['CreationTimestamp']),
			created_by = row['CreatedBy'],
			modification_timestamp = self.pandas_timestamp_todb(row['ModificationTimestamp']),
			modified_by = row['ModifiedBy']
		)
		
	def shotgun_pool(self, row):
		ShotgunPool.objects.create(
			id = int(row['Shotgun_Pool_pk'][3:]),
			name = row['Shotgun_Pool_Name'],
			technician = row['Shotgun_Pool_Technician'],
			date = self.pandas_timestamp_todb_date(row['Shotgun_Pool_Date']),
			
			creation_timestamp = self.pandas_timestamp_todb(row['CreationTimestamp']),
			created_by = row['CreatedBy'],
			modification_timestamp = self.pandas_timestamp_todb(row['ModificationTimestamp']),
			modified_by = row['ModifiedBy']
		)
		
	def shotgun_sequencing_run(self, row):
		ShotgunSequencingRun.objects.create(
			id = int(row['Shotgun_Seq_Run_pk'][3:]),
			name = row['Shotgun_Seq_Run_Name'],
			technician = row['Shotgun_Seq_Technician'],
			date = self.pandas_timestamp_todb_date(row['Shotgun_Seq_Date']),
			
			creation_timestamp = self.pandas_timestamp_todb(row['CreationTimestamp']),
			created_by = row['CreatedBy'],
			modification_timestamp = self.pandas_timestamp_todb(row['ModificationTimestamp']),
			modified_by = row['ModifiedBy']
		)
		
	def nuclear_capture_plate(self, row):
		try:
			protocol_foreign = NuclearCaptureProtocol.objects.get(id=int(row['Nuclear_Capture_Protocol_ID_fk'][3:]))
		except (NuclearCaptureProtocol.DoesNotExist, ValueError) as e:
			protocol_foreign = None
		
		NuclearCapturePlate.objects.create(
			id = int(row['Nuclear_Capture_Plate_pk'][3:]),
			name = row['Nuclear_Capture_Plate_Name'],
			enrichment_type = row['Nuclear_Capture_Enrichment_Type'],
			protocol = protocol_foreign,
			technician = row['Nuclear_Capture_Technician'],
			date = self.pandas_timestamp_todb_date(row['Nuclear_Capture_Date']),
			robot = row['Nuclear_Capture_Robot'],
			hyb_wash_temps= row['Hyb_Wash_Temps'],
			
			creation_timestamp = self.pandas_timestamp_todb(row['CreationTimestamp']),
			created_by = row['CreatedBy'],
			modification_timestamp = self.pandas_timestamp_todb(row['ModificationTimestamp']),
			modified_by = row['ModifiedBy']
		)
		
	def nuclear_sequencing_run(self, row):
		NuclearSequencingRun.objects.create(
			id = int(row['Nuclear_Sequencing_Run_pk'][3:]),
			name = row['Nuclear_Seq_Run_Name'],
			technician = row['Nuclear_Seq_Run_Technician'],
			date = self.pandas_timestamp_todb_date(row['Nuclear_Seq_Run_Date']),
			
			creation_timestamp = self.pandas_timestamp_todb(row['CreationTimestamp']),
			created_by = row['CreatedBy'],
			modification_timestamp = self.pandas_timestamp_todb(row['ModificationTimestamp']),
			modified_by = row['ModifiedBy']
		)
		
	def radiocarbon_shipment(self, row):
		RadiocarbonShipment.objects.create(
			ship_id = row['AMS_Ship_ID_pk'],
			ship_date = self.pandas_timestamp_todb_date(row['AMS_Ship_Date']),
			analysis_lab = row['Analysis_Lab'],
			
			creation_timestamp = self.pandas_timestamp_todb(row['CreationTimestamp']),
			created_by = row['CreatedBy'],
			modification_timestamp = self.pandas_timestamp_todb(row['ModificationTimestamp']),
			modified_by = row['ModifiedBy']
		)
		
	def radiocarbon_dating_invoice(self, row):
		RadiocarbonDatingInvoice.objects.create(
			invoice_number = row['Invoice_Number_pk'],
			company_name = row['Company_Name'],
			billing_period = row['Billing_Period'],
			billing_date = self.pandas_timestamp_todb_date(row['Billing_Date']),
			item_description = row['Item_Description'],
			number_of_samples = self.int_or_null(row['Number_of_Samples']),
			total_charge = Decimal('{:.2f}'.format(float(row['Total_Charge']))),
			note = row['Billing_Note'],

			creation_timestamp = self.pandas_timestamp_todb(row['CreationTimestamp']),
			created_by = row['CreatedBy'],
			modification_timestamp = self.pandas_timestamp_todb(row['ModificationTimestamp']),
			modified_by = row['ModifiedBy']
		)
		
	def radiocarbon_dated_sample(self, row):
		# foreign keys for nullable fields
		try:
			invoice_number = row['Invoice_Number_fk']
			invoice_foreign = RadiocarbonDatingInvoice.objects.get(invoice_number=invoice_number)
		except (RadiocarbonDatingInvoice.DoesNotExist, ValueError) as e:
			invoice_foreign = None
			
		try:
			radiocarbon_shipment = row['AMS_Ship_ID_fk']
			radiocarbon_shipment_foreign = RadiocarbonShipment.objects.get(ship_id=radiocarbon_shipment)
		except (RadiocarbonShipment.DoesNotExist, ValueError) as e:
			radiocarbon_shipment_foreign = None
		
		RadiocarbonDatedSample.objects.create(
			id = int(row['Dated_Sample_ID_pk'][2:]),
			sample = Sample.objects.get(reich_lab_id=int(row['Sample_ID_fk'][1:])),
			radiocarbon_shipment = radiocarbon_shipment_foreign,
			notes = row['AMS_Notes'],
			material = row['Material'],
			fraction_modern = self.float_or_null(row['Fraction_Modern']),
			fraction_modern_plus_minus = self.float_or_null(row['Fraction_Modern_Plus_Minus']),
			d14c_per_mille = self.float_or_null(row['D14C_Per_Mille']),
			d14c_per_mille_plus_minus = self.float_or_null(row['D14C_Per_Mille_Plus_Minus']),
			age_14c_bp = self.float_or_null(row['Age_14C_BP']),
			age_14c_bp_plus_minus = self.float_or_null(row['Age_14C_BP_Plus_Minus']),
			delta13c_per_mille = self.float_or_null(row['Delta13C_Per_Mille']),
			delta15n_per_mille = self.float_or_null(row['Delta15N_Per_Mille']),
			percent_carbon = self.float_or_null(row['Percent_Carbon']),
			percent_nitrogen = self.float_or_null(row['Percent_Nitrogen']),
			carbon_to_nitrogen_ratio = self.float_or_null(row['Carbon_to_Nitrogen_Ratio']),
			run_date = self.pandas_timestamp_todb_date(row['Run_Date']),
			lab_code = row['Lab_Code'],
			payment_lab = row['Payment_Lab'],
			invoice = invoice_foreign,
			
			creation_timestamp = self.pandas_timestamp_todb(row['CreationTimestamp']),
			created_by = row['CreatedBy'],
			modification_timestamp = self.pandas_timestamp_todb(row['ModificationTimestamp']),
			modified_by = row['ModifiedBy']
		)
		
	# publication
	
	def distributions_shipment(self, row):
		DistributionsShipment.objects.create(
			id = int(row['Distribution_Shipment_ID_pk'][2:]),
			collaborator = Collaborator.objects.get(id=int(row['Collaborator_ID_fk'][1:])),
			date = self.pandas_timestamp_todb_date(row['Distribution_Date']),
			shipment_method = row['Shipment_Method'],
			shipment_tracking_number = row['Shipment_Tracking_Number'],
			shipment_notes = row['Shipment_Notes'],
			delivery_date = self.pandas_timestamp_todb_date(row['Delivery_Date']),
			delivery_notes = row['Delivery_Notes'],

			creation_timestamp = self.pandas_timestamp_todb(row['CreationTimestamp']),
			created_by = row['CreatedBy'],
			modification_timestamp = self.pandas_timestamp_todb(row['ModificationTimestamp']),
			modified_by = row['ModifiedBy']
		)
		
	def distributions_lysate(self, row):
		DistributionsLysate.objects.create(
			id = int(row['Lysate_Distribution_ID_pk'][2:]),
			distribution_shipment = DistributionsShipment.objects.get(id=int(row['Distribution_Shipment_ID_fk'][2:])),
			lysate = Lysate.objects.get(lysate_id__startswith=row['Lysate_ID_fk']),
			lysate_sent_ul = float(row['uL_Lysate_Sent']),
			
			creation_timestamp = self.pandas_timestamp_todb(row['CreationTimestamp']),
			created_by = row['CreatedBy'],
			modification_timestamp = self.pandas_timestamp_todb(row['ModificationTimestamp']),
			modified_by = row['ModifiedBy']
		)
		
	# Nothing in this table
	'''
	def distributions_extract(self, row):
		DistributionsExtract.objects.create(
			
		)
	'''
		
	def results(self, row):
		# foreign keys for nullable fields
		try:
			mt_capture_plate_foreign = MTCapturePlate.objects.get(id=int(row['MT_Capture_Plate_fk'][4:]))
		except (MTCapturePlate.DoesNotExist, ValueError) as e:
			mt_capture_plate_foreign = None
		try:
			mt_seq_run_foreign = MTSequencingRun.objects.get(id=int(row['MT_Seq_Run_fk'][4:]))
		except (MTSequencingRun.DoesNotExist, ValueError) as e:
			mt_seq_run_foreign = None
		try:
			shotgun_pool_foreign = ShotgunPool.objects.get(id=int(row['Shotgun_Pool_fk'][3:]))
		except (ShotgunPool.DoesNotExist, ValueError) as e:
			shotgun_pool_foreign = None
		try:
			shotgun_seq_run_foreign = ShotgunSequencingRun.objects.get(id=int(row['Shotgun_Seq_Run_fk'][3:]))
		except (ShotgunSequencingRun.DoesNotExist, ValueError) as e:
			shotgun_seq_run_foreign = None
		try:
			nuclear_capture_plate_foreign = NuclearCapturePlate.objects.get(id=int(row['Nuclear_Capture_Plate_fk'][3:]))
		except (NuclearCapturePlate.DoesNotExist, ValueError) as e:
			nuclear_capture_plate_foreign = None
		try:
			nuclear_seq_run_foreign = NuclearSequencingRun.objects.get(id=int(row['Nuclear_Seq_Run_fk'][3:]))
		except (NuclearSequencingRun.DoesNotExist, ValueError) as e:
			nuclear_seq_run_foreign = None
		try:
			extract_control_foreign = ControlsExtract.objects.get(id=int(row['EC_Group_ID_fk'][2:]))
		except (ControlsExtract.DoesNotExist, ValueError) as e:
			extract_control_foreign = None
		try:
			library_control_foreign = ControlsLibrary.objects.get(id=int(row['LC_Group_ID_fk'][2:]))
		except (ControlsLibrary.DoesNotExist, ValueError) as e:
			library_control_foreign = None
			
		results_object = Results.objects.create(
			id = int(row['Results_ID_pk'][1:]),
			library_id = row['Library_ID_fk'],
			mt_capture_plate = mt_capture_plate_foreign,
			mt_seq_run = mt_seq_run_foreign,
			shotgun_pool = shotgun_pool_foreign,
			shotgun_seq_run = shotgun_seq_run_foreign,
			nuclear_capture_plate = nuclear_capture_plate_foreign,
			nuclear_seq_run = nuclear_seq_run_foreign,
			extract_control = extract_control_foreign,
			library_control = library_control_foreign,
			creation_timestamp = self.pandas_timestamp_todb(row['CreationTimestamp']),
			created_by = row['CreatedBy'],
			modification_timestamp = self.pandas_timestamp_todb(row['ModificationTimestamp']),
			modified_by = row['ModifiedBy']
		)
		
		# MT Analysis
		mt_raw = self.int_or_null(row['mtDNA_Raw_Sequences'])
		if mt_raw is not None:
			MTAnalysis.objects.create(
				parent = results_object,
				demultiplexing_sequences = mt_raw,
				sequences_passing_filters = self.int_or_null(row['mtDNA_Sequences_Passing_Filters']),
				sequences_aligning = self.int_or_null(row['mtDNA_Sequences_Target_Alignment']),
				sequences_aligning_post_dedup = self.int_or_null(row['mtDNA_Sequences_Target_Alignment_PostDedup']),
				coverage = self.float_or_null(row['mtDNA_Coverage']),
				mean_median_sequence_length = self.float_or_null(row['mtDNA_Mean_Median_Seq_Length']),
				damage_last_base = self.float_or_null(row['mtDNA_Damage_Last_Base']),
				consensus_match = self.float_or_null(row['mtDNA_Consensus_Match']),
				consensus_match_95ci = row['mtDNA_Consensus_Match_95CI'],
				haplogroup = row['mtDNA_Haplogroup'],
				haplogroup_confidence = self.float_or_null(row['mtDNA_Haplogroup_Confidence']),
				track_mt_rsrs = row['Track_mt_rsrs'],
				report = row['mtDNA_report'],

				creation_timestamp = self.pandas_timestamp_todb(row['CreationTimestamp']),
				created_by = row['CreatedBy'],
				modification_timestamp = self.pandas_timestamp_todb(row['ModificationTimestamp']),
				modified_by = row['ModifiedBy']
			)

		
		# create spike analysis if applicable
		if len(row['Spike_Track_ID']) > 0:
			SpikeAnalysis.objects.create(
				parent = results_object,
				bioinfo_processing_protocol = row['Spike_Bioinfo_Processing_Protocol'],
				spike_track_id = row['Spike_Track_ID'],
				spike_pre_aut = self.int_or_null(row['Spike_preAut']),
				spike_post_aut = self.int_or_null(row['Spike_postAut']),
				spike_post_y = self.int_or_null(row['Spike_postY']),
				spike_complexity = self.float_or_null(row['Spike_Complexity']),
				spike_sex = row['Spike_Sex'],
				screening_outcome =row['mtDNA_Screening_Outcome'], 
				
				creation_timestamp = self.pandas_timestamp_todb(row['CreationTimestamp']),
				created_by = row['CreatedBy'],
				modification_timestamp = self.pandas_timestamp_todb(row['ModificationTimestamp']),
				modified_by = row['ModifiedBy']
			)

		# Shotgun analysis
		shotgun_raw = self.int_or_null(row['Shotgun_Raw_Sequences'])
		if shotgun_raw is not None:
			ShotgunAnalysis.objects.create(
				parent = results_object,
				bioinfo_processing_protocol = row['Shotgun_Bioinfo_Processing_Protocol'],
				track_id = row['Shotgun_Track_ID'],
				raw_sequences = shotgun_raw,
				sequences_passing_filters = self.int_or_null(row['Shotgun_Sequences_Passing_Filters']),
				reads_mapped_hg19 = self.int_or_null(row['Shotgun_Reads_Mapped_HG19']),
				mean_median_sequence_length = self.float_or_null(row['Shotgun_Mean_Median_Seq_Length']),
				fraction_hg19 = self.float_or_null(row['Shotgun_Percent_HG19']),
				damage_rate = self.float_or_null(row['Shotgun_Damage_Rate']),
				fraction_hg19_hit_mtdna = self.float_or_null(row['Shotgun_Fraction_HG19_Hit_mtDNA']),
				
				creation_timestamp = self.pandas_timestamp_todb(row['CreationTimestamp']),
				created_by = row['CreatedBy'],
				modification_timestamp = self.pandas_timestamp_todb(row['ModificationTimestamp']),
				modified_by = row['ModifiedBy']
			)
		
		# nuclear analysis
		nuclear_deindexing = self.int_or_null(row['Nuclear_Raw_Reads_OR_Deindexing'])
		if nuclear_deindexing is not None:
			NuclearAnalysis.objects.create(
				parent = results_object,
				bioinfo_processing_protocol = row['Nuclear_Bioinfo_Processing_Protocol'],
				pulldown_logfile_location = row['Pulldown_Logfile_Location'],
				pulldown_1st_column_nickdb = row['Pulldown_1st_Column_NickDB'],
				pulldown_2nd_column_nickdb_alt_sample = row['Pulldown_2nd_Column_NickDB_alt_sample'],
				pulldown_3rd_column_nickdb_bam = row['Pulldown_3rd_Column_NickDB_bam'],
				pulldown_4th_column_nickdb_hetfa = row['Pulldown_4th_Column_NickDB_hetfa'],
				pulldown_5th_column_nickdb_readgroup_diploid_source = row['Pulldown_5th_Column_NickDB_readgroup_diploid_source'],
				seq_run_file_name = row['Nuclear_Seq_Run_File_Name'],
				track_id_report_file = row['Nuclear_Track_ID_Report_File'],
				raw_reads_or_deindexing = nuclear_deindexing,
				sequences_merge_pass_barcode = self.int_or_null(row['Nuclear_Sequences_Merge_Pass_Barcode']),
				target_sequences_pass_qc_predup = self.int_or_null(row['Nuclear_Target_Sequences_Pass_QC_PreDedup']),
				target_sequences_pass_qc_postdedup = self.int_or_null(row['Nuclear_Target_Sequences_Pass_QC_PostDedup']),
				unique_targets_hit = self.int_or_null(row['Nuclear_Fraction_Unique_Targets_Hit']),
				unique_snps_hit = self.int_or_null(row['Nuclear_Unique_SNPS_Hit']),
				coverage_targeted_positions = self.float_or_null(row['Nuclear_Coverage_Targeted_Positions']),
				expected_coverage_10_marginal_uniqueness = self.float_or_null(row['Nuclear_Expected_Coverage_10%_Marginal_Uniqueness']),
				expected_coverage_37_marginal_uniqueness = self.float_or_null(row['Nuclear_Expected_Coverage_37%_Marginal_Uniqueness']),
				marginal_uniqueness = self.float_or_null(row['Nuclear_Marginal_Uniqueness']),

				mean_median_seq_length = self.float_or_null(row['Nuclear_Mean_Median_Seq_Length']),
				damage_last_base = self.float_or_null(row['Nuclear_Damage_Last_Base']),

				x_hits = self.int_or_null(row['Nuclear_X_Hits']),
				y_hits = self.int_or_null(row['Nuclear_Y_Hits']),
				sex = row['Nuclear_Sex'],
				y_haplogroup = row['Nuclear_Y_Haplogroup'],
				angsd_snps = self.int_or_null(row['Nuclear_ANGSD_SNPs']),
				angsd_mean = self.float_or_null(row['Nuclear_ANGSD_Mean']),
				angsd_z = self.float_or_null(row['Nuclear_ANGSD_Z']),
				assessment = row['Assessment'],
				version_release = row['Version_Release'],
				results_note = row['Results_Note'],
				#find = row['Find'],
				
				creation_timestamp = self.pandas_timestamp_todb(row['CreationTimestamp']),
				created_by = row['CreatedBy'],
				modification_timestamp = self.pandas_timestamp_todb(row['ModificationTimestamp']),
				modified_by = row['ModifiedBy']
			)
