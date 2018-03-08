from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
import datetime
import pathlib
from sequencing_run.ssh_command import ssh_command
from sequencing_run.sample_sheet import index_barcode_key_to_fields
from sequencing_run.models import DemultiplexedSequencing, Flowcell

class Command(BaseCommand):
	help = 'load demultiplexed index-barcode bams from a sequencing run into database'
	
	def add_arguments(self, parser):
		parser.add_argument('--date_string', nargs=1)
		parser.add_argument('--name', nargs=1)
		
	def handle(self, *args, **options):
		date_string = options['date_string'][0]
		name = options['name'][0]
		date = datetime.datetime.strptime(date_string, "%Y%m%d").date()
		
		flowcell_id = self.get_flowcell_id(date_string, name)
		flowcell_obj, created = Flowcell.objects.get_or_create(flowcell=flowcell_id, sequencing_date=date, name=name)
		#print(flowcell_id)
		#print(flowcell_obj)
		#nuclear
		self.load_demultiplexed_bams_into_database(date_string, name, flowcell_obj, settings.NUCLEAR_SUBDIRECTORY, 'hg19')
		#mt
		self.load_demultiplexed_bams_into_database(date_string, name, flowcell_obj, settings.MT_SUBDIRECTORY, 'rsrs')
		

	def load_demultiplexed_bams_into_database(self, date_string, name, flowcell, subdirectory, reference):
		# read the list bam files
		command = "ls {}/{}_{}/{}".format(settings.DEMULTIPLEXED_PARENT_DIRECTORY, date_string, name, subdirectory)
		ssh_result = ssh_command(settings.COMMAND_HOST, command, None, self.stderr)
		result = ssh_result.stdout.readlines()
		for filename in result:
			filename = filename.strip() # remove trailing newlines
			# only process bam files
			#print(filename)
			if pathlib.Path(filename).suffix == '.bam':
				bam_filename = pathlib.Path(filename).name
				#print(bam_filename)
				# filename contains index-barcode key
				key = pathlib.Path(bam_filename).stem
				i5, i7, p5, p7 = index_barcode_key_to_fields(key)
				bam_path = "{}/{}_{}/{}/{}".format(settings.DEMULTIPLEXED_PARENT_DIRECTORY, date_string, name, subdirectory, bam_filename)
				sequenced, created = DemultiplexedSequencing.objects.get_or_create(flowcell = flowcell, i5_index = i5, i7_index = i7, p5_barcode = p5, p7_barcode = p7, reference = reference, path = bam_path)
			
	# Find the read group from a demultiplexed flowcell, using the contents of the Illumina fastq headers
	def get_flowcell_id(self, date_string, name):
		# if we are running on the web host, try to read the file directly
		read_groups_file_path = "{}/{}_{}/read_groups".format(settings.DEMULTIPLEXED_PARENT_DIRECTORY, date_string, name)
		try:
			with open(read_groups_file_path) as f:
				return read_flowcell_id_from_file_contents(f)
		# it looks like we are not on an orchestra/O2 web host, so ssh onto an O2 server to retrieve file
		except FileNotFound:
			command = "cat {}".format(read_groups_file_path)
			ssh_result = ssh_command(settings.COMMAND_HOST, command, None, self.stderr)
			result = ssh_result.stdout.readlines()
			return read_flowcell_id_from_file_contents(result)
		return None
	
	# Retrieve the read group from a list of lines
	def read_flowcell_id_from_file_contents(result):
		# example line:
		# PM:NS500217     PU:HWCHLBGX3.488.1
		flowcell_id = None
		for line in result:
			fields = line.split()
			platform_unit = fields[1]
			if platform_unit.startswith('PU:'):
				flowcell_id_line = platform_unit[3:].split('.')[0]
				if flowcell_id == None:
					flowcell_id = flowcell_id_line
				elif flowcell_id != flowcell_id_line:
					raise ValueError('flowcell ids do not match: {} {}'.format(flowcell_id, flowcell_id_line))
		return flowcell_id
