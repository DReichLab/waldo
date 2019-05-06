 
# Input: 
# 1. sample sheet (not needed? barcodes and indices matching are assumed to be in the same library
# 2. list of flowcells

# output
# list of bams for assembly, each line has the components to build one bam 
# demultiplexing bam lists have only bam paths
# release bam lists include library ID, experiment type, UDG treatment, etc.
from django.db.models import Q
from django.conf import settings
from .models import DemultiplexedSequencing, Flowcell, SequencingAnalysisRun, ReleasedLibrary, PositiveControlLibrary
import functools
import operator
from .ssh_command import save_file_with_contents, ssh_command, save_file_base
from .library_id import LibraryID
from .index_barcode_key import IndexBarcodeKey
import re
import os

nuclear_references = ['hg19']
mt_references = ['rsrs']

def flowcells_for_names(sequencing_run_names):
	flowcell_queryset = SequencingAnalysisRun.objects.filter(sample_set_names__name__in=sequencing_run_names).values_list('triggering_flowcells__flowcell_text_id', flat=True).order_by('id')
	flowcell_text_ids = list(flowcell_queryset)
	return flowcell_text_ids

# For a set of flowcells, generate a dictionary of bams to merge into libraries for each index-barcode combination
# separate by reference
# returns dictionaries of DemultiplexedSequencing objects
def generate_bam_lists(flowcells_text_ids):
	# query bam files produced from the argument flowcells
	q_list = [Q( ('flowcells__flowcell_text_id__exact', flowcells_text_id) ) for flowcells_text_id in flowcells_text_ids]
	# query for any bam sequenced from one of the argument flowcells
	sublibraries = DemultiplexedSequencing.objects.filter(functools.reduce(operator.or_, q_list) ).distinct()
	
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
	q_list = [Q( ('triggering_flowcells__flowcell_text_id__exact', flowcells_text_id) ) for flowcells_text_id in flowcells_text_ids]
	runs = SequencingAnalysisRun.objects.filter(functools.reduce(operator.or_, q_list)).distinct()
	file_list = ["{0}/{1}_{2}/{1}_{2}.demultiplex_statistics".format(settings.DEMULTIPLEXED_PARENT_DIRECTORY, run.sequencing_date.strftime("%Y%m%d"), run.name) for run in runs]
	output_text = '\n'.join(file_list)
	save_file_with_contents(output_text, sequencing_date_string, sequencing_run_name, 'demultiplex_statistics_list', settings.COMMAND_HOST)
	#print(output_text)

# the library ID will not match the sample parameters field if a control library
def latest_library_version(sample_parameters):
	try:
		library_id = LibraryID(sample_parameters.libraryID)
		library = ReleasedLibrary.objects.filter(sample=library_id.sample,
								 sample_suffix=library_id.sample_suffix,
								 lysis=library_id.lysis,
								 extract=library_id.extract, 
								 library=library_id.library, 
								 experiment=sample_parameters.experiment, 
								 udg=sample_parameters.udg).latest('version')
		return library.version
	except:
		library = PositiveControlLibrary.objects.filter(name__name=sample_parameters.libraryID).latest('version')
		return library.version
	
# each bam is a DemultiplexedSequencing
# In contrast to output_bam_list, this function includes sample data (experiment type, UDG treatment)
def output_bam_list_with_sample_data(bams_by_index_barcode_key, sequencing_run_name, extension, samples_parameters):
	output_text = generate_bam_list_with_sample_data(bams_by_index_barcode_key, sequencing_run_name, extension, samples_parameters)
	# make sure directory exists
	directory = "{}/{}".format(settings.RUN_RELEASE_FILES_DIRECTORY, sequencing_run_name)
	ssh_command(settings.COMMAND_HOST, "mkdir -p {}".format(directory), True, True)
	filename = "{}.{}".format(sequencing_run_name, extension)
	#print(sequencing_run_name, directory, filename)
	save_file_base(output_text, directory, filename, settings.COMMAND_HOST)

# sequencing_run_name is a single name, not a combination
def generate_bam_list_with_sample_data(bams_by_index_barcode_key, sequencing_run_name, extension, samples_parameters):
	output_lines = []
	# each line is the list arguments required for one library
	# it needs to include all of the metadata required to build read groups
	# of bam paths for one index-barcode key
	for key in bams_by_index_barcode_key:
		bam_list = bams_by_index_barcode_key[key]
		from_sample_sheet = samples_parameters[find_index_barcode_match(key, samples_parameters)]
		library_id = from_sample_sheet.libraryID
		#print(library_id)
		label = "{}_{}_{}".format(sequencing_run_name, from_sample_sheet.experiment, from_sample_sheet.udg)
		experiment = from_sample_sheet.experiment
		udg = from_sample_sheet.udg
		reference = bam_list[0].reference
		do_not_use = from_sample_sheet.do_not_use
		wetlab_notes = from_sample_sheet.wetlab_notes
		#print(label)
		
		if len(do_not_use) == 0:
			version = str(1)
			# version determination
			if library_id == settings.CONTROL_ID:
				control_name = "{}_{}".format(settings.CONTROL_ID, sequencing_run_name)
				# check for a prior version of this library
				try:
					latestControl = PositiveControlLibrary.objects.filter(name=control_name).latest('version')
					version = latestControl.version
				except:
					pass
			elif library_id == settings.CONTROL_PCR_ID:
				continue
			else:
				try:
					lib = LibraryID(library_id) # this will remove Contl libraries
					# is there a prior existing version of this library?
					prior_releases = ReleasedLibrary.objects.filter(sample=lib.sample, lysis=lib.lysis, extract=lib.extract, library=lib.library, experiment=experiment, udg=udg)
					# are there currently more libraries than in prior release?
					bam_count_by_version = { prior_release.version: len(prior_release.demultiplexedsequencing_set.all()) for prior_release in prior_releases}
					# check bam counts
					if len(bam_count_by_version) > 0:
						version_with_most_component_bams = max(bam_count_by_version, key=bam_count_by_version.get)
						if bam_count_by_version.get(version_with_most_component_bams) > len(bam_list):
							raise ValueError('version has more component bams than exist in database')
						elif bam_count_by_version.get(version_with_most_component_bams) == len(bam_list):
							version = str(version_with_most_component_bams)
						else:
							max_version = max(bam_count_by_version, key=int)
							version = max_version + 1
				except:
					print("manual versioning required for {}".format(library_id))
			# TODO record version with components
			'''
			if library_id == settings.CONTROL_ID:
				control_library_filename = "{0}.{1}.{2}.v{3:d}.bam".format(control_name, experiment, reference, version)
				control_library_fullpath = os.path.join(settings.CONTROL_LIBRARIES_DIRECTORY, control_name, control_library_filename)
				control_library, created = PositiveControlLibrary.objects.get_or_create(name=sequencing_run_name, experiment=experiment, udg=udg, path=control_library_fullpath)
				if not created:
					print('{} exists already'.format(control_name))
			'''
			
			# parse sample number and use as individual
			# at the library level, we do not know of overlaps with other individuals
			if library_id == settings.CONTROL_ID:
				library_id = control_name
				individual_id = control_name
			else:
				reg_exp_pattern = re.compile('S[\d]+')
				match_object = reg_exp_pattern.match(library_id)
				if match_object is None:
					#raise ValueError('invalid library id: cannot locate sample id')
					continue
				else:
					individual_id = match_object.group().replace('S', 'I')
					#print(individual_id)
				
			library_output_fields = [key, library_id, individual_id, label, experiment, udg, reference, version, wetlab_notes]
			
			# each bam is a DemultiplexedSequencing object
			for bam in bam_list:
				bam_date_string = bam.flowcells.order_by('sequencing_date').last().sequencing_date.strftime("%Y%m%d") # use most recent date
				#print(bam_date_string)
				#print(bam.path)
				library_output_fields.append(bam.path)
				library_output_fields.append(bam_date_string)
				if reference != bam.reference:
					raise ValueError('mismatch in references for component bams')
			
			library_line = '\t'.join(library_output_fields)
			output_lines.append(library_line)

	output_text = '\n'.join(output_lines)
	return output_text

# Check whether a index-barcode combination in the sample sheet matches the discovered combination
# For example, a control library may use B2 D2, which are portions of Q2
def index_barcode_match(index_barcode_key, samples_parameters):
	# if there is a direct match, we are done (fast)
	if index_barcode_key in samples_parameters and samples_parameters[index_barcode_key]:
		return True
	# if there is not a direct match look for subset (slow)
	result = find_index_barcode_match(index_barcode_key, samples_parameters)
	return (result != None)
	
def find_index_barcode_match(index_barcode_key, samples_parameters):
	key_object = IndexBarcodeKey.from_string(index_barcode_key)
	for key_string_from_sheet in samples_parameters:
		key_from_sheet = IndexBarcodeKey.from_string(key_string_from_sheet)
		if key_from_sheet.maps_to(key_object):
			return key_string_from_sheet
	return None
	
# this assembles only libraries on a sample sheet
def prepare_to_assemble_release_libraries(sequencing_run_name, samples_parameters):
	flowcell_text_ids = flowcells_for_names([sequencing_run_name])
	nuclear_bams_by_index_barcode_key, mt_bams_by_index_barcode_key = generate_bam_lists(flowcell_text_ids)
	
	# filter bam lists to include only samples on list
	nuclear_bams_by_filtered_index_barcode_key = {index_barcode_key: bam_filename_list for index_barcode_key, bam_filename_list in nuclear_bams_by_index_barcode_key.items() if (index_barcode_match(index_barcode_key, samples_parameters))}
	mt_bams_by_filtered_index_barcode_key = {index_barcode_key: bam_filename_list for index_barcode_key, bam_filename_list in mt_bams_by_index_barcode_key.items() if (index_barcode_match(index_barcode_key, samples_parameters))}
	
	# save bam list files to pass to cromwell
	output_bam_list_with_sample_data(nuclear_bams_by_filtered_index_barcode_key, sequencing_run_name, 'nuclear.release.bamlist', samples_parameters)
	output_bam_list_with_sample_data(mt_bams_by_filtered_index_barcode_key, sequencing_run_name, 'mt.release.bamlist', samples_parameters)
