from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
import datetime
import pathlib
import re
from sequencing_run.ssh_command import ssh_command
from sequencing_run.sample_sheet import index_barcode_key_to_fields
from sequencing_run.models import DemultiplexedSequencing, Flowcell, SequencingAnalysisRun

from sequencing_run.assemble_libraries import prepare_to_assemble_libraries
from sequencing_run.analysis import start_cromwell, ANALYSIS_COMMAND_LABEL

class Command(BaseCommand):
	help = 'load demultiplexed index-barcode bams from a sequencing run into database'
	
	def add_arguments(self, parser):
		parser.add_argument('--date_string', required=True)
		parser.add_argument('--name', required=True)
		parser.add_argument('--analysis_run', type=int, required=True)
		parser.add_argument('--start_analysis', action='store_true', help='start analysis after loading bams')
		parser.add_argument('--flowcell_by_lane', action='store_true', help='set to split flowcells into lanes. Used for Broad HiSeq or NovaSeq')
		parser.add_argument('--nuclear_subdirectory', help='directory for nuclear files under demultiplex directory')
		parser.add_argument('--mt_subdirectory', help='directory for mt files under demultiplex directory')
		
	def handle(self, *args, **options):
		date_string = options['date_string']
		name = options['name']
		date = datetime.datetime.strptime(date_string, "%Y%m%d").date()
		start_analysis = options['start_analysis']
		flowcell_by_lane = options['flowcell_by_lane']
		nuclear_subdirectory = options['nuclear_subdirectory'] if options['nuclear_subdirectory'] else settings.NUCLEAR_SUBDIRECTORY
		mt_subdirectory = options['mt_subdirectory'] if options['mt_subdirectory'] else settings.MT_SUBDIRECTORY
		
		# save flowcell for this SequencingAnalysisRun
		flowcell_text_ids = self.get_flowcell_text_ids(date_string, name, flowcell_by_lane)
		flowcell_objs = []
		for flowcell_text_id in flowcell_text_ids:
			flowcell_obj, created = Flowcell.objects.get_or_create(flowcell_text_id=flowcell_text_id, sequencing_date=date)
			flowcell_objs.append(flowcell_obj)
			#print(flowcell_text_id)
			#print(flowcell_obj)
			
		# save the flowcell(s) as part of the analysis run, if there is one
		# make this optional so we can add demultiplexing results without having to start from interface
		try:
			if options['analysis_run']:
				analysis_run_id = options['analysis_run']
				analysis_run = SequencingAnalysisRun.objects.get(id=analysis_run_id)
				for flowcell_obj in flowcell_objs:
					analysis_run.triggering_flowcells.add(flowcell_obj)
				analysis_run.save()
				#print(analysis_run_id)
		except SequencingAnalysisRun.DoesNotExist:
			pass
		
		# add demultiplexed bams to database
		#nuclear
		# TODO identify reference properly
		self.load_demultiplexed_bams_into_database(date_string, name, flowcell_objs, nuclear_subdirectory, 'hg19')
		#mt
		self.load_demultiplexed_bams_into_database(date_string, name, flowcell_objs, mt_subdirectory, 'rsrs')
		
		if start_analysis:
			analysis_run = SequencingAnalysisRun.objects.get(id=analysis_run_id)
			flowcell_text_ids += [flowcell_object.flowcell_text_id for flowcell_object in analysis_run.prior_flowcells_for_analysis.all()]
			prepare_to_assemble_libraries(date_string, name, flowcell_text_ids)
			start_result = start_cromwell(date_string, name, ANALYSIS_COMMAND_LABEL)
			# retrieve SLURM job number from output
			for line in start_result.stdout.readlines():
				self.stdout.write(line)
				m = re.match('Submitted batch job[\s]+(\d+)', line)
				if m is not None:
					analysis_run.slurm_job_number = int(m.group(1))
			analysis_run.processing_state = SequencingAnalysisRun.RUNNING_ANALYSIS
			analysis_run.save()
		

	def load_demultiplexed_bams_into_database(self, date_string, name, flowcells, subdirectory, reference):
		# read the list bam files
		directory_str = "{}/{}_{}/{}".format(settings.DEMULTIPLEXED_PARENT_DIRECTORY, date_string, name, subdirectory)
		pathlist = pathlib.Path(directory_str).glob("*.bam")
		for filename in pathlist:
			#print(filename)
			bam_filename = filename.name
			#print(bam_filename)
			# filename contains index-barcode key
			key = filename.stem
			i5, i7, p5, p7 = index_barcode_key_to_fields(key)
			bam_path = "{}/{}_{}/{}/{}".format(settings.DEMULTIPLEXED_PARENT_DIRECTORY, date_string, name, subdirectory, bam_filename)
			sequenced, created = DemultiplexedSequencing.objects.get_or_create(i5_index = i5, i7_index = i7, p5_barcode = p5, p7_barcode = p7, reference = reference, path = bam_path)
			for flowcell in flowcells:
				sequenced.flowcells.add(flowcell)
			sequenced.save()
			self.stderr.write('{}\tcreated: {}'.format(bam_filename, str(created)))
			
	# Find the flowcell text id from a demultiplexed flowcell, using the contents of the Illumina fastq headers
	def get_flowcell_text_ids(self, date_string, name, flowcell_by_lane):
		# if we are running on the web host, try to read the file directly
		read_groups_file_path = "{}/{}_{}/read_groups".format(settings.DEMULTIPLEXED_PARENT_DIRECTORY, date_string, name)
		# now try with nonshortened
		try:
			with open(read_groups_file_path) as f:
				return self.read_flowcell_text_ids_from_file_contents(f, flowcell_by_lane)
		except FileNotFoundError:
			# it looks like we are not on an orchestra/O2 web host, so ssh onto an O2 server to retrieve file
			command = "cat {}".format(read_groups_file_path)
			ssh_result = ssh_command(settings.COMMAND_HOST, command, None, self.stderr)
			result = ssh_result.stdout.readlines()
			return self.read_flowcell_text_ids_from_file_contents(result, flowcell_by_lane)
		return None
	
	# Retrieve the flowcell ID(s) from a list of lines
	# flowcell_by_lane is a boolean indicating whether to include lane numbers in IDs
	# output will look like 'HWCHLBGX3' or 'HWCHLBGX3.1' depending on this boolean
	def read_flowcell_text_ids_from_file_contents(self, result, flowcell_by_lane):
		# example line:
		# PM:NS500217     PU:HWCHLBGX3.488.1
		flowcell_text_ids = []
		for line in result:
			fields = line.split()
			platform_unit = fields[1]
			if platform_unit.startswith('PU:'):
				platform_unit_fields = re.split('\.|\n', platform_unit[3:])
				flowcell_text_id = platform_unit_fields[0]
				lane = platform_unit_fields[2]
				if flowcell_by_lane:
					flowcell_text_id +=  '.{}'.format(lane)
				if flowcell_text_id not in flowcell_text_ids:
					flowcell_text_ids.append(flowcell_text_id)
		return flowcell_text_ids
