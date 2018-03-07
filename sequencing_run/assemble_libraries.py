 
# Input: 
# 1. sample sheet (not needed? barcodes and indices matching are assumed to be in the same library
# 2. list of flowcells

# output
# assembled bam files
from django.db.models import Q
from django.conf import settings
from sequencing_run.models import DemultiplexedSequencing
import functools
import operator
from sequencing_run.barcode_prep import save_file_with_contents

nuclear_references = ['hg19']
mt_references = ['rsrs']

# For the argument flowcells, build files with each line containing a list of bam files to assemble for one index-barcode key
def prepare_to_assemble_libraries(sequencing_date_string, sequencing_run_name, flowcells_text_ids):
	# query bam files produced from the argument flowcells
	q_list = [Q( ('flowcell__flowcell__exact', flowcells_text_id) ) for flowcells_text_id in flowcells_text_ids]
	# query for any bam sequenced from one of the argument flowcells
	sublibraries = DemultiplexedSequencing.objects.filter(functools.reduce(operator.or_, q_list) )
	
	# construct maps indexed by index-barcode keys to assemble lists of bams to merge
	nuclear_bams_by_index_barcode_key = {}
	mt_bams_by_index_barcode_key = {}
	
	for bam in sublibraries:
		key = "{}_{}_{}_{}".format(bam.i5_index, bam.i7_index, bam.p5_barcode, bam.p7_barcode)
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
		
	output_bam_list(nuclear_bams_by_index_barcode_key, sequencing_date_string, sequencing_run_name, 'nuclear')
	output_bam_list(mt_bams_by_index_barcode_key, sequencing_date_string, sequencing_run_name, 'mt')
		
# generate file with list of bams for library on each line and save it in run directory
def output_bam_list(bams_by_index_barcode_key, sequencing_date_string, sequencing_run_name, reference_type):
	# each line is the list of bam paths for one index-barcode key
	bam_lists = bams_by_index_barcode_key.values()
	# flatten each list into tab delimited line of 
	bam_text_lists = ['\t'.join(map(lambda bam : bam.path, bam_list)) for bam_list in bam_lists]
	output_text = '\n'.join(bam_text_lists)
	
	save_file_with_contents(output_text, sequencing_date_string, sequencing_run_name, '{}.bamlist'.format(reference_type), settings.COMMAND_HOST)
	#print(output_text)
	
