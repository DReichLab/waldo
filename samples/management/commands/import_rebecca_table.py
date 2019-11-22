from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from datetime import datetime, timedelta, timezone
import pandas
from pandas import ExcelFile
from samples.models import Collaborator

from sequencing_run.assemble_libraries import flowcells_for_names, generate_bam_lists, generate_bam_list_with_sample_data, index_barcode_match

class Command(BaseCommand):
	help = 'Import table from Rebecca'
	
	def add_arguments(self, parser):
		parser.add_argument("table_type")
		parser.add_argument("spreadsheet", help="Excel spreadsheet containing")
		
	def handle(self, *args, **options):
		process_row_map = {
			'collaborator': self.collaborator,
		}
		
		spreadsheet = options['spreadsheet']
		process_row = process_row_map[options['table_type'].lower()]
		
		df = pandas.read_excel(spreadsheet)
		df = df.fillna('') # replace NaN with empty string

		for index, row in df.iterrows():
			process_row(row)
			
	def timestring_todb(self, datetime_string):
		eastern_daylight_timedelta = timedelta(hours=-4)
		local_datetime = datetime.strptime(datetime_string, "%m/%d/%Y %H:%M:%S")
		utc_datetime_naive = local_datetime - eastern_daylight_timedelta
		utc_datetime_aware = utc_datetime_naive.replace(tzinfo=timezone.utc)
		return utc_datetime_aware
	
	def pandas_timestamp_todb(self, pandas_timestamp):
		eastern_daylight_timedelta = timedelta(hours=-4)
		local_datetime = pandas_timestamp.to_pydatetime()
		utc_datetime_naive = local_datetime - eastern_daylight_timedelta
		utc_datetime_aware = utc_datetime_naive.replace(tzinfo=timezone.utc)
		return utc_datetime_aware

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
			harvard_ari_approval = bool(row.get('Harvard_ARI_Approval', False)),
			creation_timestamp = self.pandas_timestamp_todb(row['CreationTimestamp']),
			created_by = row['CreatedBy'],
			modification_timestamp = self.pandas_timestamp_todb(row['ModificationTimestamp']),
			modified_by = row['ModifiedBy']
			)
