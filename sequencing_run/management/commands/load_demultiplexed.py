from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
import datetime
import pathlib
from sequencing_run.ssh_command import ssh_command
from sequencing_run.sample_sheet import index_barcode_key_to_fields
from sequencing_run.models import DemultiplexedSequencing, Flowcell, SequencingAnalysisRun

from sequencing_run.assemble_libraries import prepare_to_assemble_libraries
from sequencing_run.analysis import start_cromwell, analysis_command_label

class Command(BaseCommand):
	help = 'load demultiplexed index-barcode bams from a sequencing run into database'
	
	def add_arguments(self, parser):
		parser.add_argument('--date_string', nargs=1)
		parser.add_argument('--name', nargs=1)
		parser.add_argument('--analysis_run', type=int, nargs=1)
		parser.add_argument('--start_analysis', action='store_true', help='start analysis after loading bams')
		
	def handle(self, *args, **options):
		date_string = options['date_string'][0]
		name = options['name'][0]
		date = datetime.datetime.strptime(date_string, "%Y%m%d").date()
		start_analysis = options['start_analysis']
		
		flowcell_text_id = self.get_flowcell_text_id(date_string, name)
		flowcell_obj, created = Flowcell.objects.get_or_create(flowcell_text_id=flowcell_text_id, sequencing_date=date, name=name)
		#print(flowcell_text_id)
		#print(flowcell_obj)
		
		# save the flowcell as part of the analysis run, if there is one
		# make this optional so we can add demultiplexing results without having to start from interface
		try:
			if options['analysis_run']:
				analysis_run_id = options['analysis_run'][0]
				analysis_run = SequencingAnalysisRun.objects.get(id=analysis_run_id)
				analysis_run.triggering_flowcell = flowcell_obj.id
				analysis_run.save()
				#print(analysis_run_id)
		except SequencingAnalysisRun.DoesNotExist:
			pass
		
		# add demultiplexed bams to database
		#nuclear
		#self.load_demultiplexed_bams_into_database(date_string, name, flowcell_obj, settings.NUCLEAR_SUBDIRECTORY, 'hg19')
		#mt
		#self.load_demultiplexed_bams_into_database(date_string, name, flowcell_obj, settings.MT_SUBDIRECTORY, 'rsrs')
		
		if start_analysis:
			analysis_run = SequencingAnalysisRun.objects.get(id=analysis_run_id)
			flowcell_text_ids = [flowcell_object.flowcell_text_id for flowcell_object in analysis_run.prior_flowcells_for_analysis.all()]
			flowcell_text_ids.append(flowcell_text_id)
			prepare_to_assemble_libraries(date_string, name, flowcell_text_ids)
			start_cromwell(date_string, name, analysis_command_label)
		

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
				sequenced, created = DemultiplexedSequencing.objects.get_or_create(flowcell_text_id = flowcell, i5_index = i5, i7_index = i7, p5_barcode = p5, p7_barcode = p7, reference = reference, path = bam_path)
			
	# Find the flowcell text id from a demultiplexed flowcell, using the contents of the Illumina fastq headers
	def get_flowcell_text_id(self, date_string, name):
		# if we are running on the web host, try to read the file directly
		read_groups_file_path = "{}/{}_{}/read_groups".format(settings.DEMULTIPLEXED_PARENT_DIRECTORY, date_string, name)
		# try with removing the leading /n of directory in case we are on orchestra and not O2
		try:
			if read_groups_file_path.startswith('/n/'):
				shortened_read_groups_file_path = read_groups_file_path[2:]
				with open(shortened_read_groups_file_path) as f:
					return self.read_flowcell_text_id_from_file_contents(f)
		except FileNotFoundError:
			pass
		# now try with nonshortened
		try:
			with open(read_groups_file_path) as f:
				return self.read_flowcell_text_id_from_file_contents(f)
		except FileNotFoundError:
			# it looks like we are not on an orchestra/O2 web host, so ssh onto an O2 server to retrieve file
			command = "cat {}".format(read_groups_file_path)
			ssh_result = ssh_command(settings.COMMAND_HOST, command, None, self.stderr)
			result = ssh_result.stdout.readlines()
			return self.read_flowcell_text_id_from_file_contents(result)
		return None
	
	# Retrieve the read group from a list of lines
	def read_flowcell_text_id_from_file_contents(self, result):
		# example line:
		# PM:NS500217     PU:HWCHLBGX3.488.1
		flowcell_text_id = None
		for line in result:
			fields = line.split()
			platform_unit = fields[1]
			if platform_unit.startswith('PU:'):
				flowcell_text_id_line = platform_unit[3:].split('.')[0]
				if flowcell_text_id == None:
					flowcell_text_id = flowcell_text_id_line
				elif flowcell_text_id != flowcell_text_id_line:
					raise ValueError('flowcell ids do not match: {} {}'.format(flowcell_text_id, flowcell_text_id_line))
		return flowcell_text_id
