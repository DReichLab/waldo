from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
import datetime
from sequencing_run.ssh_command import ssh_command
from sequencing_run.assemble_libraries import prepare_to_assemble_release_libraries
from sequencing_run.report_match_samples import readSampleSheet

from sequencing_run.assemble_libraries import flowcells_for_names, generate_bam_lists, generate_bam_list_with_sample_data, prepare_to_assemble_release_libraries

class Command(BaseCommand):
	help = 'Approve a set of libraries for release'
	
	def add_arguments(self, parser):
		parser.add_argument('--name', required=True)
		parser.add_argument('--sample_sheet', required=True)
		parser.add_argument('--legacy_ess', action='store_true')
		# Add an option to support 'split-lane' seq runs - will find all reports for the seq run
		parser.add_argument('--split_lanes', action='store_true')
		
	def handle(self, *args, **options):
		name = options['name']
		sample_sheet_filename = options['sample_sheet']
		adna2 = not(options['legacy_ess'])
		split_lanes = options['split_lanes']
		
		samples_parameters = readSampleSheet(sample_sheet_filename, adna2)
		#for s in samples_parameters:
		#	print(s, samples_parameters[s])
		nu = prepare_to_assemble_release_libraries(name, samples_parameters, split_lanes)
		self.stderr.write('{} finished release preparation'.format(name))
		'''
		sequencing_run_name = name

		flowcell_text_ids = flowcells_for_names([sequencing_run_name])
		nuclear_bams_by_index_barcode_key, mt_bams_by_index_barcode_key = generate_bam_lists(flowcell_text_ids)
		
		# filter bam lists to include only samples on list
		# This does not match control libraries, which do not have the full Q barcode sets
		nuclear_bams_by_filtered_index_barcode_key = {index_barcode_key: bam_filename_list for index_barcode_key, bam_filename_list in nuclear_bams_by_index_barcode_key.items() if (index_barcode_key in samples_parameters and samples_parameters[index_barcode_key])}
		out = generate_bam_list_with_sample_data(nuclear_bams_by_filtered_index_barcode_key, sequencing_run_name, 'nuclear.release.bamlist', samples_parameters)
		print(out)
		'''
