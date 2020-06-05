from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from samples.anno import library_anno_line
from samples.pipeline import udg_and_strandedness, set_timestamps, ReportEntry

from samples.models import Results, Library
from sequencing_run.models import MTAnalysis

import re

def load_mt_capture_fields(library_id, report_fields, report_headers, release_label, sequencing_run_name, damage_restricted):
	try:
		results = Results.objects.get(library_id__exact=library_id, mt_seq_run__name__iexact=sequencing_run_name)
	except Results.DoesNotExist as e:
		print('{} not found for load_mt_capture_fields'.format(library_id), file=sys.stderr)
		raise e
	library = Library.objects.get(reich_lab_library_id = library_id)
	udg, strandedness = udg_and_strandedness(library)
	
	now = timezone.now()
	entry = ReportEntry(report_headers, report_fields)
	# MTAnalysis
	mt = MTAnalysis.objects.get(parent = results, damage_restricted = damage_restricted)
	'''
	mt.demultiplexing_sequences = entry.get('raw', int)
	mt.sequences_passing_filters = entry.get('merged', int)
	mt.sequences_aligning = entry.get('MT_pre', int)
	mt.sequences_aligning_post_dedup = entry.get('MT_post', int)
	'''
	mt.coverage = entry.get('MT_post-coverage', float)
	#mt.mean_median_sequence_length = entry.get('mean_rsrs', float)
	
	try:
		damage_rsrs_ct1 = entry.get('damage_rsrs_ct1', float)
		damage_rsrs_ga1 = entry.get('damage_rsrs_ga1', float)
		if strandedness == 'ds':
			mt.damage_last_base = (damage_rsrs_ct1 + damage_rsrs_ga1) / 2
		elif strandedness == 'ss':
			mt.damage_last_base = damage_rsrs_ct1
		else:
			raise ValueError('bad strandedness {}'.format(standedness))
	except:
		mt.damage_last_base = None
	
	mt.consensus_match = entry.get('contamination_contammix', float)
	
	try:
		contamination_contammix_lower = entry.get('contamination_contammix_lower', float)
		contamination_contammix_upper = entry.get('contamination_contammix_upper', float)
		mt.consensus_match_95ci = '[{:.3f}, {:.3f}]'.format(contamination_contammix_lower, contamination_contammix_upper)
	except:
		mt.consensus_match_95ci = ''
		
	mt.haplogroup = entry.get('MT_Haplogroup', str)
	mt.haplogroup_confidence = entry.get('MT_Haplogroup_rank', float)
	#mt.track_mt_rsrs = 
	#mt.report = 
	set_timestamps(mt, False, now)
	mt.save()

class Command(BaseCommand):
	help = "Update the MT-related entries from a merge analysis"
	
	def add_arguments(self, parser):
		parser.add_argument('merge_results')
		parser.add_argument('-l', '--release_label', required=True)
		parser.add_argument('-n', '--sequencing_run_name', required=True)
		
	def handle(self, *args, **options):
		merge_list_filename = options['merge_results']
		release_label = options['release_label']
		sequencing_run_name = options['sequencing_run_name']
		damage_restricted = False
		
		with open(merge_list_filename) as f:
			header_line = f.readline()
			headers = re.split('\t|\n', header_line)
			for line in f:
				fields = re.split('\t|\n', line)
				library_id = fields[headers.index('ID')]
				
				load_mt_capture_fields(library_id, fields, headers, release_label, sequencing_run_name, damage_restricted)
