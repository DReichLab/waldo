from django.utils import timezone
from .models import Results
from .anno import individual_from_library_id
from sequencing_run.models import AnalysisFiles, MTAnalysis, NuclearAnalysis, ShotgunAnalysis
from sequencing_run.library_id import LibraryID

import re
from pathlib import Path

bioinfo_processing_protocol = 'Matt'

# TODO rewrite model creation to take defaults in get_or_create

def set_timestamps(timestamped_object, was_created, update_time, user='mym11'):
	if was_created:
		timestamped_object.created_by = user
		timestamped_object.creation_timestamp = update_time
	timestamped_object.modification_timestamp = update_time
	timestamped_object.modified_by = user

# Convenience class for accessing fields from the pipeline report to handle missing values
class ReportEntry:
	def __init__(self, report_headers, report_fields, fail_on_field_failures=False):
		self.report_headers = report_headers
		self.report_fields = report_fields
		self.fail_on_field_failures = fail_on_field_failures
		
	def get(self, desired_header, field_type):
		try:
			return field_type(self.report_fields[self.report_headers.index(desired_header)])
		except Exception as e:
			if self.fail_on_field_failures:
				raise e
			else:
				return None

def load_mt_capture_fields(library_id, report_fields, report_headers, release_label, sequencing_run_name):
	results = Results.objects.get(library_id__exact=library_id, mt_seq_run__name__iexact=sequencing_run_name)
	
	now = timezone.now()
	entry = ReportEntry(report_headers, report_fields)
	# MTAnalysis
	mt, mt_created = MTAnalysis.objects.get_or_create(parent = results)
	mt.demultiplexing_sequences = entry.get('raw', int)
	mt.sequences_passing_filters = entry.get('merged', int)
	mt.sequences_aligning = entry.get('MT_pre', int)
	mt.sequences_aligning_post_dedup = entry.get('MT_post', int)
	mt.coverage = entry.get('MT_post-coverage', float)
	mt.mean_median_sequence_length = entry.get('mean_rsrs', float)
	
	try:
		damage_rsrs_ct1 = entry.get('damage_rsrs_ct1', float)
		damage_rsrs_ga1 = entry.get('damage_rsrs_ga1', float)
		mt.damage_last_base = (damage_rsrs_ct1 + damage_rsrs_ga1) / 2
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
	set_timestamps(mt, mt_created, now)
	mt.save()

def load_nuclear_capture_fields(library_id, report_fields, report_headers, release_label, sequencing_run_name):
	results = Results.objects.get(library_id__exact=library_id, nuclear_seq_run__name__iexact=sequencing_run_name)
	
	now = timezone.now()
	entry = ReportEntry(report_headers, report_fields)
	# NuclearAnalysis
	nuclear, nuclear_created = NuclearAnalysis.objects.get_or_create(parent = results, version_release = release_label)
	
	nuclear.bioinfo_processing_protocol = bioinfo_processing_protocol
	
	#seq_run_file_name = models.CharField(max_length=150) # TODO no idea what this is
	#track_id_report_file = models.CharField(max_length=160)
	nuclear.raw_reads_or_deindexing = entry.get('raw', int)
	nuclear.sequences_merge_pass_barcode = entry.get('merged', int)
	
	try:
		z1240k_pre_x = entry.get('1240k_pre_x', int)
		z1240k_pre_y = entry.get('1240k_pre_y', int)
		z1240k_pre_autosome = entry.get('1240k_pre_autosome', int)
		nuclear.target_sequences_pass_qc_predup = z1240k_pre_x + z1240k_pre_y + z1240k_pre_autosome
	except:
		pass
	
	try:
		z1240k_post_x = entry.get('1240k_post_x', int)
		z1240k_post_y = entry.get('1240k_post_y', int)
		z1240k_post_autosome = entry.get('1240k_post_autosome', int)
		nuclear.target_sequences_pass_qc_postdedup = z1240k_post_x + z1240k_post_y + z1240k_post_autosome
		
		num_1240k_autosome_targets = 1150639
		nuclear.coverage_targeted_positions = z1240k_post_autosome / num_1240k_autosome_targets
	except:
		pass
	
	nuclear.expected_coverage_10_marginal_uniqueness = entry.get('preseq_coverage_at_marginal_uniqueness_0.10', float)
	nuclear.expected_coverage_37_marginal_uniqueness = entry.get('preseq_coverage_at_marginal_uniqueness_0.368', float)
	nuclear.marginal_uniqueness = entry.get('preseq_marginal_uniqueness', float)
	nuclear.mean_median_seq_length = entry.get('mean_nuclear', float)
	
	try:
		damage_nuclear_ct1 = entry.get('damage_nuclear_ct1', float)
		damage_nuclear_ga1 = entry.get('damage_nuclear_ga1', float)
		nuclear.damage_last_base = (damage_nuclear_ct1 + damage_nuclear_ga1) / 2
	except:
		pass
	
	nuclear.x_hits = entry.get('1240k_post_x', int)
	nuclear.y_hits = entry.get('1240k_post_y', int)
	nuclear.sex = entry.get('1240k_post_sex', str)
	#nuclear.y_haplogroup = 
	nuclear.angsd_snps = entry.get('angsd_nsites', int)
	nuclear.angsd_mean = entry.get('angsd_MoM', float)
	
	try:
		angsd_MoM = entry.get('angsd_MoM', float)
		angsd_SE = entry.get('angsd_SE(MoM)', float)
		nuclear.angsd_z = angsd_MoM / angsd_SE
	except:
		pass
	
	#nuclear.assessment =
	nuclear.version_release = release_label
	#nuclear.results_note =
	set_timestamps(nuclear, nuclear_created, now)
	nuclear.save()
	
def load_shotgun_fields(library_id, report_fields, report_headers, release_label, sequencing_run_name):
	results = Results.objects.get(library_id__exact=library_id, shotgun_seq_run__name__iexact=sequencing_run_name)
	
	now = timezone.now()
	entry = ReportEntry(report_headers, report_fields)
	
	shotgun, shotgun_created = ShotgunAnalysis.objects.get_or_create(parent = results)
	shotgun.bioinfo_processing_protocol = bioinfo_processing_protocol
	#shotgun.track_id =
	shotgun.raw_sequences = entry.get('raw', int)
	shotgun.sequences_passing_filters = entry.get('merged', int)
	
	try:
		autosome_pre = entry.get('autosome_pre', int)
		X_pre = entry.get('X_pre', int)
		Y_pre = entry.get('Y_pre', int)
		MT_pre = entry.get('MT_pre', int)
		
		shotgun.reads_mapped_hg19 = autosome_pre + X_pre + Y_pre + MT_pre
		shotgun.fraction_hg19_hit_mtdna = MT_pre / (autosome_pre + X_pre + Y_pre + MT_pre)
	except:
		pass
	
	shotgun.mean_median_sequence_length = entry.get('mean_nuclear', float)
	shotgun.fraction_hg19 = entry.get('endogenous_pre', float)
	
	try:
		damage_nuclear_ct1 = entry.get('damage_nuclear_ct1', float)
		damage_nuclear_ga1 = entry.get('damage_nuclear_ga1', float)
		shotgun.damage_rate = (damage_nuclear_ct1 + damage_nuclear_ga1) / 2
	except:
		pass
	
	set_timestamps(shotgun, shotgun_created, now)
	shotgun.save()

def load_pipeline_report(report_filename, desired_experiment, release_label, sequencing_run_name):
	with open(report_filename) as f:
		f.readline() # first line is read count
		header_line = f.readline() # second line is header fields
		headers = re.split('\t|\n', header_line)
		
		report_library_id_index = headers.index('library_id')
		experiment_index = headers.index('experiment')
		
		# each line is one library
		# iterate through report libraries and update corresponding library info
		for line in f:
			fields = re.split('\t|\n', line)
			
			library_id = fields[report_library_id_index]
			experiment = fields[experiment_index]
			if library_id.startswith('S'): # is not '' and library_id is not 'Contl.Capture':				
				if len(fields) == len(headers): # no data will have fewer fields than headers
					if desired_experiment in experiment:
						load_mt_capture_fields(library_id, fields, headers, release_label, sequencing_run_name)
						load_nuclear_capture_fields(library_id, fields, headers, release_label, sequencing_run_name)
					elif 'Raw' in experiment:
						load_shotgun_fields(library_id, fields, headers, release_label, sequencing_run_name)
						
# diagnostic check for results objects
def test_results_exist(pulldown_stdout, sequencing_run_name):
	with open(pulldown_stdout) as f:
		for line in f:
			if 'mean depth' in line:
				fields = line.split()
				if fields[2] != 'mean' or fields[3] != 'depth:' or fields[5] != 'coverage:' or fields[0] != fields[1]:
					raise ValueError('Parse problem in pulldown stdout: {}'.format(line))
				library_id = fields[0]
				
				try:
					results = Results.objects.get(library_id__exact=library_id, nuclear_seq_run__name__iexact=sequencing_run_name)
				except Results.DoesNotExist as e:
					print('No Results object for {}'.format(library_id))
						
# load the contents of Nick's pulldown stdout files for
# mean depth (coverage)
# coverage (number of SNPs hit)
# Pulldown stdout does not contain _d identifiers. We rewrite these when merging.
def load_pulldown_stdout(pulldown_stdout, release_label, sequencing_run_name, damage_restricted):
	with open(pulldown_stdout) as f:
		for line in f:
			if 'mean depth' in line:
				fields = line.split()
				if fields[2] != 'mean' or fields[3] != 'depth:' or fields[5] != 'coverage:' or fields[0] != fields[1]:
					raise ValueError('Parse problem in pulldown stdout: {}'.format(line))
				library_id = fields[0]
				instance_id, library_id_obj = individual_from_library_id(library_id)
				coverage = float(fields[4])
				snps_hit = int(fields[6])
				
				results = Results.objects.get(library_id__exact=library_id, nuclear_seq_run__name__iexact=sequencing_run_name)
				
				nuclear, nuclear_created = NuclearAnalysis.objects.get_or_create(parent = results, version_release = release_label, damage_restricted = damage_restricted)
				
				nuclear.coverage_targeted_positions = coverage
				nuclear.unique_snps_hit = snps_hit
				nuclear.pulldown_logfile_location = Path(pulldown_stdout).resolve()
				set_timestamps(nuclear, nuclear_created, timezone.now())
				nuclear.save()
				
				analysis_files, analysis_files_created = AnalysisFiles.objects.get_or_create(parent = results)
				analysis_files.bioinfo_processing_protocol = bioinfo_processing_protocol
				# these are from pulldown, not report
				analysis_files.pulldown_1st_column_nickdb = instance_id
				#.pulldown_2nd_column_nickdb_alt_sample = 
				#.pulldown_4th_column_nickdb_hetfa = models.CharField(max_length=100)
				set_timestamps(analysis_files, analysis_files_created, timezone.now())
				analysis_files.save()
				

# load bam location and read groups from pulldown dblist file
# dblist does not contain _d damage restricted library ids
# fields saved from the dblist are independent of damage restriction
def load_pulldown_dblist(dblist, release_label, sequencing_run_name):
	with open(dblist) as f:
		for line in f:
			fields = line.split()
			if fields[0] != fields[1]:
				raise ValueError('Parse problem in pulldown dblist: {}'.format(line))
			library_id = fields[0]
			bam_path = fields[2]
			read_groups = fields[3]
			
			results = Results.objects.get(library_id__exact=library_id, nuclear_seq_run__name__iexact=sequencing_run_name)
			
			analysis_files, analysis_files_created = AnalysisFiles.objects.get_or_create(parent = results)
			
			# TODO should be a more robust way of loading other paths
			analysis_files.mt_bam = bam_path.replace('hg19', 'rsrs') 
			analysis_files.nuclear_bam = bam_path
			
			analysis_files.pulldown_3rd_column_nickdb_bam = bam_path
			analysis_files.pulldown_5th_column_nickdb_readgroup_diploid_source = read_groups
			set_timestamps(analysis_files, analysis_files_created, timezone.now())
			analysis_files.save()
