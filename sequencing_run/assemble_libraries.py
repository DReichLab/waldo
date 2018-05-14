 
# Input: 
# 1. sample sheet (not needed? barcodes and indices matching are assumed to be in the same library
# 2. list of flowcells

# output
# assembled bam files
from django.db.models import Q
from django.conf import settings
from sequencing_run.models import DemultiplexedSequencing, Flowcell, SequencingAnalysisRun
import functools
import operator
from .ssh_command import save_file_with_contents
import re

nuclear_references = ['hg19']
mt_references = ['rsrs']

def flowcells_for_names(sequencing_run_names):
	flowcell_queryset = SequencingAnalysisRun.objects.filter(sample_set_names__name__in=sequencing_run_names).values_list('triggering_flowcell__flowcell_text_id', flat=True).order_by('id')
	flowcell_text_ids = list(flowcell_queryset)
	return flowcell_text_ids

# For a set of flowcells, generate a list of bams to merge into libraries for each index-barcode combination
# separate by reference
# returns list of DemultiplexedSequencing objects
def generate_bam_lists(flowcells_text_ids):
	# query bam files produced from the argument flowcells
	q_list = [Q( ('flowcell__flowcell_text_id__exact', flowcells_text_id) ) for flowcells_text_id in flowcells_text_ids]
	# query for any bam sequenced from one of the argument flowcells
	sublibraries = DemultiplexedSequencing.objects.filter(functools.reduce(operator.or_, q_list) )
	
	# construct maps indexed by index-barcode keys to assemble lists of bams to merge
	nuclear_bams_by_index_barcode_key = {}
	mt_bams_by_index_barcode_key = {}
	
	for bam in sublibraries:
		key = "{}_{}_{}_{}".format(bam.i5_index, bam.i7_index, bam.p5_barcode, bam.p7_barcode)
		# each demultiplexed bam is aligned to either the nuclear (hg19) or the MT (rsrs) reference
		if bam.reference in nuclear_references:
			if key not in nuclear_bams_by_index_barcode_key:
				nuclear_bams_by_index_barcode_key[key] = []
			bam_list_for_key = nuclear_bams_by_index_barcode_key.get(key)
			bam_list_for_key.append(bam)
		elif bam.reference in mt_references:
			if key not in mt_bams_by_index_barcode_key:
				mt_bams_by_index_barcode_key[key] = []
			bam_list_for_key = mt_bams_by_index_barcode_key.get(key)
			bam_list_for_key.append(bam)
		else:
			raise ValueError("{} is not a reference currently handled while assembling libraries".format(bam.reference))
	return nuclear_bams_by_index_barcode_key, mt_bams_by_index_barcode_key

# For the argument flowcells, build files with each line containing a list of bam files to assemble for one index-barcode key
def prepare_to_assemble_libraries(sequencing_date_string, sequencing_run_name, flowcells_text_ids):
	nuclear_bams_by_index_barcode_key, mt_bams_by_index_barcode_key = generate_bam_lists(flowcells_text_ids)
		
	output_bam_list(nuclear_bams_by_index_barcode_key, sequencing_date_string, sequencing_run_name, 'nuclear.bamlist')
	output_bam_list(mt_bams_by_index_barcode_key, sequencing_date_string, sequencing_run_name, 'mt.bamlist')
	output_demultiplex_statistics(sequencing_date_string, sequencing_run_name, flowcells_text_ids)
		
# generate file with list of bams for library on each line and save it in run directory
# each bam is a DemultiplexedSequencing
def output_bam_list(bams_by_index_barcode_key, sequencing_date_string, sequencing_run_name, extension):
	# each line is the list of bam paths for one index-barcode key
	bam_lists = bams_by_index_barcode_key.values()
	# flatten each list into tab delimited line of bam paths
	bam_text_lists = ['\t'.join(map(lambda bam : bam.path, bam_list)) for bam_list in bam_lists]
	output_text = '\n'.join(bam_text_lists)
	
	save_file_with_contents(output_text, sequencing_date_string, sequencing_run_name, extension, settings.COMMAND_HOST)
	#print(output_text)
	
# generate a file that contains the demultiplex statistics for the flowcells
def output_demultiplex_statistics(sequencing_date_string, sequencing_run_name, flowcells_text_ids):
	#print(flowcells_text_ids)
	q_list = [Q( ('triggering_flowcell__flowcell_text_id__exact', flowcells_text_id) ) for flowcells_text_id in flowcells_text_ids]
	runs = SequencingAnalysisRun.objects.filter(functools.reduce(operator.or_, q_list))
	file_list = ["{0}/{1}_{2}/{1}_{2}.demultiplex_statistics".format(settings.DEMULTIPLEXED_PARENT_DIRECTORY, run.sequencing_date.strftime("%Y%m%d"), run.name) for run in runs]
	output_text = '\n'.join(file_list)
	save_file_with_contents(output_text, sequencing_date_string, sequencing_run_name, 'demultiplex_statistics_list', settings.COMMAND_HOST)
	#print(output_text)
	
# each bam is a DemultiplexedSequencing
# In contrast to output_bam_list, this function includes sample data (experiment type, UDG treatment)
def output_bam_list_with_sample_data(bams_by_index_barcode_key, sequencing_date_string, sequencing_run_name, extension, samples_parameters):
	output_lines = []
	# each line is the list arguments required for one library
	# it needs to include all of the metadata required to build read groups
	# of bam paths for one index-barcode key
	for key in bams_by_index_barcode_key:
		bam_list = bams_by_index_barcode_key[key]
		library_id = samples_parameters[key].libraryID
		#print(library_id)
		label = "{}_{}_{}".format(sequencing_run_name, samples_parameters[key].experiment, samples_parameters[key].udg)
		experiment = samples_parameters[key].experiment
		udg = samples_parameters[key].udg
		reference = bam_list[0].reference
		version = str(1) # TODO
		#print(label)
		
		# parse sample number and use as individual
		reg_exp_pattern = re.compile('S[\d]+')
		match_object = reg_exp_pattern.match(library_id)
		if match_object is None:
			raise ValueError('invalid library id: cannot locate sample id')
		else:
			individual_id = match_object.group().replace('S', 'I')
			#print(individual_id)
			
		library_output_fields = [key, library_id, individual_id, label, experiment, udg, reference, version]
		
		for bam in bam_list:
			bam_date_string = bam.flowcell.sequencing_date.strftime("%Y%m%d")
			#print(bam_date_string)
			#print(bam.path)
			library_output_fields.append(bam.path)
			library_output_fields.append(bam_date_string)
			if reference != bam.reference:
				raise ValueError('mismatch in references for component bams')
		
		library_line = '\t'.join(library_output_fields)
		output_lines.append(library_line)

	output_text = '\n'.join(output_lines)
	save_file_with_contents(output_text, sequencing_date_string, sequencing_run_name, extension, settings.COMMAND_HOST)
	
# this assembles only libraries on a sample sheet
def prepare_to_assemble_release_libraries(sequencing_date_string, sequencing_run_name, flowcells_text_ids, samples_parameters):
	nuclear_bams_by_index_barcode_key, mt_bams_by_index_barcode_key = generate_bam_lists(flowcells_text_ids)
	
	# filter bam lists to include only samples on list
	nuclear_bams_by_filtered_index_barcode_key = {index_barcode_key: bam_filename_list for index_barcode_key, bam_filename_list in nuclear_bams_by_index_barcode_key.items() if (index_barcode_key in samples_parameters and samples_parameters[index_barcode_key])}
	mt_bams_by_filtered_index_barcode_key = {index_barcode_key: bam_filename_list for index_barcode_key, bam_filename_list in mt_bams_by_index_barcode_key.items() if (index_barcode_key in samples_parameters and samples_parameters[index_barcode_key])}
	
	# save bam list files to pass to cromwell
	output_bam_list_with_sample_data(nuclear_bams_by_filtered_index_barcode_key, sequencing_date_string, sequencing_run_name, 'nuclear.release.bamlist', samples_parameters)
	output_bam_list_with_sample_data(mt_bams_by_filtered_index_barcode_key, sequencing_date_string, sequencing_run_name, 'mt.release.bamlist', samples_parameters)
