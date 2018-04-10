from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
import datetime
from sequencing_run.ssh_command import ssh_command
from sequencing_run.assemble_libraries import flowcells_for_names,  prepare_to_assemble_release_libraries
from sequencing_run.report_match_samples import readSampleSheet

class Command(BaseCommand):
	help = 'Approve a set of libraries for release'
	
	def add_arguments(self, parser):
		parser.add_argument('--date_string', nargs=1)
		parser.add_argument('--name', nargs=1)
		parser.add_argument('--sample_sheet', nargs=1)
		
	def handle(self, *args, **options):
		date_string = options['date_string'][0]
		name = options['name'][0]
		date = datetime.datetime.strptime(date_string, "%Y%m%d").date()
		sample_sheet_filename = options['sample_sheet'][0]
		
		samples_parameters = readSampleSheet(sample_sheet_filename)
		flowcell_text_ids = flowcells_for_names([name])
		#for flowcell_text_id in flowcell_text_ids:
		#	self.stdout.write(flowcell_text_id)
		nu = prepare_to_assemble_release_libraries(date_string, name, flowcell_text_ids, samples_parameters)
		
		for key in nu:
			bam_list = nu[key]
			# DemultiplexedSequencing objects
			bam_filename_list = [bam.path for bam in bam_list]
			self.stdout.write("{}\t{}".format(key, "\t".join(bam_filename_list)))
