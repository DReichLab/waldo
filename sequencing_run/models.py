from django.db import models

from samples.models import Timestamped, Results, AssessmentCategory, DataInstance
import samples.models

# Create your models here.

# This should really be called an Illumina directory
class SequencingRun(models.Model):
	illumina_directory = models.CharField(max_length=255, unique=True)
	
	def __str__(self):
		return self.illumina_directory

# These are the names attached to sequencing runs. 
# For each name, there may be multiple sequencing runs covering the same set of samples
class SequencingRunID(models.Model):
	name = models.CharField(max_length=50)
	order = models.IntegerField() # order from Zhao's db
	
	def __str__(self):
		return self.name

# Largest unit of flowcell with sample sheet
# This may be the whole flowcell with all lanes for NextSeq
# Or a single lane for X10 or NovaSeq
class Flowcell(models.Model):
	flowcell_text_id = models.CharField("flowcell", max_length=20, unique=True)
	sequencing_date = models.DateField()
	
	def __str__(self):
		return '{} {}'.format(self.sequencing_date, self.flowcell_text_id)

class SequencingAnalysisRun(models.Model):
	STARTED = 0
	COPYING_SEQUENCING_DATA = 100
	PREPARING_JSON_INPUTS = 200
	PREPARING_RUN_SCRIPT = 300
	DEMULTIPLEXING = 400
	RUNNING_ANALYSIS = 500
	RUNNING_ANALYSIS_PRELIMINARY_REPORT_DONE = 600
	FINISHED = 1000
	FAILED = -1
	
	ANALYSIS_RUN_STATES = (
		(STARTED, 'started'),
		(COPYING_SEQUENCING_DATA, 'copying sequencing data to Orchestra/O2'),
		(PREPARING_JSON_INPUTS, 'preparing json inputs'),
		(PREPARING_RUN_SCRIPT, 'preparing run script'),
		(DEMULTIPLEXING, 'demultiplexing and aligning'),
		(RUNNING_ANALYSIS, 'running analysis'),
		(RUNNING_ANALYSIS_PRELIMINARY_REPORT_DONE, 'running analysis, preliminary report ready'),
		(FINISHED, 'finished'),
		(FAILED, 'failed')
	)
	
	name = models.CharField("sequencing run name", max_length=100)
	start = models.DateTimeField("sequencing run processing run start time")
	processing_state = models.IntegerField(default=0, choices=ANALYSIS_RUN_STATES)
	# pooled sequencing runs have multiple names
	# non-pooled sequencing runs have only one
	sample_set_names = models.ManyToManyField(SequencingRunID, through='OrderedSequencingRunID')
	
	sequencing_run = models.ForeignKey(SequencingRun, on_delete=models.CASCADE)
	sequencing_date = models.DateField()
	slurm_job_number = models.IntegerField(null=True)
	top_samples_to_demultiplex = models.IntegerField()
	# new data to analyze
	triggering_flowcells = models.ManyToManyField(Flowcell, related_name='input_flowcells')
	# old data to combine with new data
	prior_flowcells_for_analysis = models.ManyToManyField(Flowcell)
	
# through model for labeling SequencingAnalysisRun with multiple SequencingRunID names and sorting
class OrderedSequencingRunID(models.Model):
	sequencing_analysis_run = models.ForeignKey(SequencingAnalysisRun, on_delete=models.CASCADE)
	name = models.ForeignKey(SequencingRunID, on_delete=models.CASCADE)
	interface_order = models.IntegerField()
	
	class Meta:
		ordering = ["interface_order"]
		unique_together = (("sequencing_analysis_run", "interface_order"),)

class Library(models.Model):
	experiment = models.CharField(max_length=20)
	udg = models.CharField(max_length=10)
	workflow = models.CharField(max_length=100)
	reference = models.CharField(max_length=30)
	path = models.CharField(max_length=300)
	release_time = models.DateTimeField("release time", auto_now_add=True)
	version = models.IntegerField()
	
	class Meta:
		abstract = True
	
# a library may comprise multiple demultiplexed bams from different sequencing runs
class ReleasedLibrary(Library):
	sample = models.IntegerField()
	sample_suffix = models.CharField(max_length=5, default='')
	lysis = models.IntegerField(null=True)
	extract = models.IntegerField(null=True)
	library = models.IntegerField()
	
	class Meta:
		unique_together = (("sample", "sample_suffix", "lysis", "extract", "library", "experiment", "udg", "reference", "version"),)
		
class ReleasedLibrary2(models.Model):
	library = models.ForeignKey(samples.models.Library, on_delete=models.PROTECT)
	version = models.PositiveSmallIntegerField(default=1)
		
# Each positive control library in each capture is marked with Contl.Capture
class PositiveControlLibrary(Library):
	name = models.ForeignKey(SequencingRunID, on_delete=models.PROTECT)
	
	class Meta:
		unique_together = (("name", "version"),)

# a demultiplexed, aligned bam with no associated sample/library/extract information
class DemultiplexedSequencing(models.Model):
	flowcells = models.ManyToManyField(Flowcell, related_name='source_flowcells')
	i5_index = models.CharField(max_length=10)
	i7_index = models.CharField(max_length=10)
	p5_barcode = models.CharField(max_length=40, blank=True)
	p7_barcode = models.CharField(max_length=40, blank=True)
	reference = models.CharField(max_length=30)
	path = models.CharField(max_length=300)
	library = models.ManyToManyField(ReleasedLibrary) # this needs to be many-to-many to support versions

class AnalysisFiles(Timestamped):
	parent = models.ForeignKey(Results, on_delete=models.CASCADE)
	bioinfo_processing_protocol = models.CharField(max_length=20, blank=True)
	mt_bam = models.CharField(max_length=300, blank=True)
	mt_fasta = models.CharField(max_length=300, blank=True)
	nuclear_bam = models.CharField(max_length=300, blank=True)
	shotgun_bam = models.CharField(max_length=300, blank=True)
	
	pulldown_1st_column_nickdb = models.CharField(max_length=50, blank=True)
	pulldown_2nd_column_nickdb_alt_sample = models.CharField(max_length=50, blank=True)
	pulldown_3rd_column_nickdb_bam = models.CharField(max_length=200, blank=True)
	pulldown_4th_column_nickdb_hetfa = models.CharField(max_length=100, blank=True)
	pulldown_5th_column_nickdb_readgroup_diploid_source = models.TextField(blank=True)

class MTAnalysis(Timestamped):
	parent = models.ForeignKey(Results, on_delete=models.CASCADE)
	demultiplexing_sequences = models.BigIntegerField(null=True)
	sequences_passing_filters = models.BigIntegerField(null=True)
	sequences_aligning = models.BigIntegerField(null=True)
	sequences_aligning_post_dedup = models.BigIntegerField(null=True)
	coverage = models.FloatField(null=True)
	mean_median_sequence_length = models.FloatField(null=True)
	damage_last_base = models.FloatField(null=True)
	consensus_match = models.FloatField(null=True)
	consensus_match_95ci = models.CharField(max_length=30, blank=True)
	haplogroup = models.CharField(max_length=30, blank=True)
	haplogroup_confidence = models.FloatField(null=True)
	track_mt_rsrs = models.CharField(max_length=160, blank=True)
	report = models.CharField(max_length=35, blank=True)
	damage_restricted = models.BooleanField(default=False)
	
class SpikeAnalysis(Timestamped):
	parent = models.ForeignKey(Results, on_delete=models.CASCADE)
	bioinfo_processing_protocol = models.CharField(max_length=50, blank=True)
	spike_track_id = models.CharField(max_length=150, blank=True)
	spike_pre_aut = models.IntegerField(null=True)
	spike_post_aut = models.IntegerField(null=True)
	spike_post_y = models.IntegerField(null=True)
	spike_complexity = models.FloatField(null=True)
	spike_sex = models.CharField(max_length=30, blank=True)
	screening_outcome = models.CharField(max_length=50, blank=True)
	damage_restricted = models.BooleanField(default=False)

class ShotgunAnalysis(Timestamped):
	parent = models.ForeignKey(Results, on_delete=models.CASCADE)
	bioinfo_processing_protocol = models.CharField(max_length=50, blank=True)
	track_id = models.CharField(max_length=150, blank=True)
	raw_sequences = models.BigIntegerField(null=True)
	sequences_passing_filters = models.BigIntegerField(null=True)
	reads_mapped_hg19 = models.BigIntegerField(null=True)
	mean_median_sequence_length = models.FloatField(null=True)
	fraction_hg19 = models.FloatField(null=True)
	damage_rate = models.FloatField(null=True)
	fraction_hg19_hit_mtdna = models.FloatField(null=True)
	damage_restricted = models.BooleanField(default=False)
	
class NuclearAnalysis(Timestamped):
	parent = models.ForeignKey(Results, on_delete=models.CASCADE)
	bioinfo_processing_protocol = models.CharField(max_length=20, blank=True)
	seq_run_file_name = models.CharField(max_length=150, blank=True) # TODO no idea what this is
	track_id_report_file = models.CharField(max_length=160, blank=True)
	raw_reads_or_deindexing = models.BigIntegerField(null=True)
	sequences_merge_pass_barcode = models.BigIntegerField(null=True)
	target_sequences_pass_qc_predup = models.BigIntegerField(null=True)
	target_sequences_pass_qc_postdedup = models.BigIntegerField(null=True)
	unique_targets_hit = models.IntegerField(null=True)
	unique_snps_hit = models.IntegerField(null=True)
	coverage_targeted_positions = models.FloatField(null=True)
	expected_coverage_10_marginal_uniqueness = models.FloatField(null=True)
	expected_coverage_37_marginal_uniqueness = models.FloatField(null=True)
	marginal_uniqueness = models.FloatField(null=True)
	mean_median_seq_length = models.FloatField(null=True)
	damage_last_base = models.FloatField(null=True)
	x_hits = models.IntegerField(null=True)
	y_hits = models.IntegerField(null=True)
	sex = models.CharField(max_length=30, blank=True)
	y_haplogroup = models.CharField(max_length=80, blank=True)
	angsd_snps = models.IntegerField(null=True)
	angsd_mean = models.FloatField(null=True)
	angsd_z = models.FloatField(null=True)
	assessment = models.ForeignKey(AssessmentCategory, null=True, on_delete=models.SET_NULL)
	assessment_notes = models.TextField(blank=True)
	version_release = models.CharField(max_length=20)
	results_note = models.TextField(blank=True)
	find = models.TextField(blank=True)
	pulldown_logfile_location = models.CharField(max_length=300, blank=True)
	damage_restricted = models.BooleanField(default=False)

class SNPSet(models.Model):
	name = models.CharField(max_length=30, unique=True, null=False, blank=False)
	description = models.TextField(blank=True)
	count = models.PositiveIntegerField(help_text='Simple count of SNPs comprising this set.')

deamination_help = "{} prime {} transitions as measured by Nick's mkdeamin program on forward strand at {}"
# shared base class for both nuclear and MT analysis
class AnalysisBase(Timestamped):
	damage_restricted = models.BooleanField(default=False)
	damage_5ct1 = models.FloatField(null=True, help_text=deamination_help.format(5, 'C->T', 'last base'))
	damage_5ct2 = models.FloatField(null=True, help_text=deamination_help.format(5, 'C->T', 'second to last base'))
	damage_3ga1 = models.FloatField(null=True, help_text=deamination_help.format(3, 'G->A', 'last base'))
	damage_3ga2 = models.FloatField(null=True, help_text=deamination_help.format(3, 'G->A', 'second to last base'))
	damage_3ct1 = models.FloatField(null=True, help_text=deamination_help.format(3, 'C->T', 'last base'))
	damage_3ct2 = models.FloatField(null=True, help_text=deamination_help.format(3, 'C->T', 'second to last base'))
	median_length = models.DecimalField(null=True, max_digits=4, decimal_places=1)
	mean_length = models.DecimalField(null=True, max_digits=4, decimal_places=1)
	indel_rate = models.FloatField(null=True)
	
class NuclearAnalysis2(AnalysisBase):
	angsd_snps = models.IntegerField(null=True)
	angsd_mean = models.FloatField(null=True)
	angsd_z = models.FloatField(null=True)
	angsd_ml_mean = models.FloatField(null=True)
	angsd_ml_z = models.FloatField(null=True)
	
	autosome_post = models.BigIntegerField(null=True, help_text='reads aligning to chromosomes 1-22 post-deduplication')
	autosome_post_coverage = models.FloatField(null=True, help_text='coverage of autosomes based on total bases in reads post-deduplication')
	x_post = models.BigIntegerField(null=True, help_text='reads aligning to X chromosome post-deduplication')
	x_post_coverage = models.FloatField(null=True, help_text='coverage of X chromosome based on total bases in reads post-deduplication')
	y_post = models.BigIntegerField(null=True, help_text='reads aligning to Y chromosome post-deduplication')
	y_post_coverage = models.FloatField(null=True, help_text='coverage of Y chromosome based on total bases in reads post-deduplication')
	
	x_autosome_ratio_lower = models.FloatField(null=True, help_text='ratio of reads covering 1240k targets X:autosome lower 95% confidence bound')
	x_autosome_ratio_upper = models.FloatField(null=True, help_text='ratio of reads covering 1240k targets X:autosome upper 95% confidence bound')
	y_autosome_ratio_lower = models.FloatField(null=True, help_text='ratio of reads covering 1240k targets Y:autosome upper 95% confidence bound')
	y_autosome_ratio_upper = models.FloatField(null=True, help_text='ratio of reads covering 1240k targets Y:autosome upper 95% confidence bound')
	yx_ratio_lower = models.FloatField(null=True, help_text='ratio of reads covering 1240k targets Y:X upper 95% confidence bound')
	yx_ratio_upper = models.FloatField(null=True, help_text='ratio of reads covering 1240k targets Y:X upper 95% confidence bound')
	c21_autosome_ratio_lower = models.FloatField(null=True, help_text='ratio of reads covering 1240k targets chromosome 21 : other autosome lower 95% confidence bound')
	c21_autosome_ratio_upper = models.FloatField(null=True, help_text='ratio of reads covering 1240k targets chromosome 21 : other autosome upper 95% confidence bound')
	
	# hapROH
	max_roh = models.FloatField(null=True)
	roh_num_4cm = models.PositiveSmallIntegerField(null=True)
	roh_sum_4cm = models.FloatField(null=True)
	roh_num_8cm = models.PositiveSmallIntegerField(null=True)
	roh_sum_8cm = models.FloatField(null=True)
	roh_num_12cm = models.PositiveSmallIntegerField(null=True)
	roh_sum_12cm = models.FloatField(null=True)
	roh_num_20cm = models.PositiveSmallIntegerField(null=True)
	roh_sum_20cm = models.FloatField(null=True)
	
	# hapcon autosome
	hapconautosome_blocks = models.PositiveSmallIntegerField(null=True)
	hapconautosome_length = models.FloatField(null=True, help_text='Total length of ROH after trimming')
	hapconautosome_contamination = models.FloatField(help_text='MLE for contamination using BFGS')
	hapconautosome_contamination_lower = models.FloatField(help_text='MLE for contamination using BFGS, confidence interval lower bound')
	hapconautosome_contamination_upper = models.FloatField(help_text='MLE for contamination using BFGS, confidence interval upper bound')

	
class HapconXAnalysis(Timestamped):
	nuclear = models.ForeignKey(NuclearAnalysis2, null=False, on_delete=models.CASCADE)
	african = models.BooleanField(help_text='True if African haplotypes are included in the reference panel. False if African haplotypes are excluded, which is the hapConX default.')
	major_reads_at_flanking_sites = models.IntegerField()
	minor_reads_at_flanking_sites = models.IntegerField()
	major_reads_at_focal_sites = models.IntegerField()
	minor_reads_at_focal_sites = models.IntegerField()
	err_rate_at_flanking_sites = models.FloatField()
	err_rate_at_focal_sites = models.FloatField()
	estimated_genotyping_error_by_flanking_sites = models.FloatField()
	number_of_sites_covered_by_at_least_one_read = models.IntegerField()
	fraction_covered = models.FloatField()
	estimated_contamination_rate = models.FloatField()
	
# This is supplemental for libraries but does not make sense for multiple libraries
class LibraryAnalysis(Timestamped):
	nuclear = models.ForeignKey(NuclearAnalysis2, null=False, on_delete=models.CASCADE)
	demultiplexed = models.BigIntegerField(help_text='Number of reads demultiplexing for this library')
	merged = models.BigIntegerField(help_text='For paired-end reads, the number of reads successfully merging')
	merge_overlap = models.PositiveSmallIntegerField(null=True, help_text='number of overlapping bases required for merging paired-end reads')
	merge_minimum_length = models.PositiveSmallIntegerField(null=True, help_text='minimum insert size to keep')
	mismatch_quality_threshold = models.PositiveSmallIntegerField(null=True, help_text='One mismatches at or above this threshold is allowed for a merge. Three mismatches are allowed below it.')
	oligo = models.IntegerField(null=True)
	
	expected_coverage_10_marginal_uniqueness = models.FloatField()
	expected_coverage_37_marginal_uniqueness = models.FloatField()
	marginal_uniqueness = models.FloatField()
	
	#endogenous = models.FloatField(null=True, help_text='(reads aligning to autosome + X + Y + MT) / merged reads')
	autosome_pre = models.BigIntegerField(null=True, help_text='reads aligning to chromosomes 1-22 pre-deduplication')
	autosome_pre_coverage = models.FloatField(null=True, help_text='coverage of autosomes based on total bases in reads pre-deduplication')
	x_pre = models.BigIntegerField(null=True, help_text='reads aligning to chromosome X pre-deduplication')
	x_pre_coverage = models.FloatField(null=True, help_text='coverage of X chromosome based on total bases in reads pre-deduplication')
	y_pre = models.BigIntegerField(null=True, help_text='reads aligning to chromosome Y pre-deduplication')
	y_pre_coverage = models.FloatField(null=True, help_text='coverage of Y chromosome based on total bases in reads pre-deduplication')
	mt_pre = models.BigIntegerField(null=True, help_text='reads aligning to MT pre-deduplication')
	duplicates_nuclear = models.BigIntegerField(null=True, help_text='nuclear reads marked as duplicates')
	duplicates_mt = models.BigIntegerField(null=True, help_text='MT reads marked as duplicates')
	
	def endogenous(self):
		return (self.autosome_pre + self.x_pre + self.y_pre + self.mt_pre) / self.merged
		
	def endogenous_cost(self):
		return (self.autosome_pre + self.x_pre + self.y_pre + self.mt_pre) / self.demultiplexed
	

class SNPCount(Timestamped):
	analysis = models.ForeignKey(NuclearAnalysis2, on_delete=models.CASCADE)
	snps = models.ForeignKey(SNPSet, on_delete=models.PROTECT)
	unique_hits = models.IntegerField()
	total_hits = models.IntegerField(help_text='Hits on SNP targets including multiple. Divide by number of targets to get coverage.')
	deduplicated = models.BooleanField(default=True)
	method = models.TextField()
	
class Pulldown(Timestamped):
	analysis= models.ForeignKey(NuclearAnalysis2, on_delete=models.CASCADE)
	snps = models.ForeignKey(SNPSet, on_delete=models.PROTECT)
	parameter_file = models.TextField()
	histmake_log = models.TextField()
	histmake_version = models.TextField()
	damage_score_log = models.TextField()
	damage_score_version = models.TextField()
	pullit_log = models.TextField()
	pullit_version = models.TextField()
	
class MTAnalysis2(AnalysisBase):
	consensus_match = models.FloatField(null=True, help_text='contammix match to consensus estimate for MT contamination')
	consensus_match_95ci_lower = models.FloatField(null=True, help_text='95% confidence interval lower bound for contammix')
	consensus_match_95ci_upper = models.FloatField(null=True, help_text='95% confidence interval upper bound for contammix')
	contammix_gelman = models.FloatField(null=True)
	contammix_inferred_error = models.FloatField(null=True)
	
	mt_post = models.IntegerField(null=True, help_text='reads aligning to MT post-deduplication')
	mt_post_coverage = models.FloatField(null=True, help_text='coverage of MT based on total bases in reads post-deduplication')
	
class HaplogroupCaller(Timestamped):
	haplogroup_type = models.CharField(max_length=10, blank=False, help_text='Y, MT, etc.')
	name = models.CharField(max_length=100, blank=False, unique=True)
	description = models.TextField(blank=True)
	
class MTHaplogroupCall(Timestamped):
	caller = models.ForeignKey(HaplogroupCaller, on_delete=models.PROTECT)
	analysis = models.ForeignKey(MTAnalysis2, on_delete=models.PROTECT)
	haplogroup = models.CharField(max_length=30, null=False, blank=False)
	rank = models.PositiveSmallIntegerField(null=True)
	quality = models.FloatField(null=True, help_text='[0.5, 1] where 1 is perfect')
	polys_found = models.TextField(blank=True)
	polys_notfound = models.TextField(blank=True)
	polys_remaining = models.TextField(blank=True)

# This is the master entry
class GeneticAnalysis(Timestamped):
	data_instance = models.ForeignKey(DataInstance, on_delete=models.PROTECT)
	genetic_id = models.CharField(max_length=40, blank=False, unique=True, db_index=True)
	nuclear_analysis = models.ForeignKey(NuclearAnalysis2, null=True, on_delete=models.CASCADE)
	mt_analysis = models.ForeignKey(MTAnalysis2, null=True, on_delete=models.CASCADE)
	assessment = models.ForeignKey(AssessmentCategory, null=True, on_delete=models.SET_NULL)
	assessment_notes = models.TextField(blank=True)
	first_release = models.PositiveSmallIntegerField(null=True, help_text='First major release where this analysis appears')
	genotype_hash = models.CharField(null=True, blank=False, max_length=8)
	missingness_hash = models.CharField(null=True, blank=False, max_length=9)
	
class FamilyRelationshipDegree(models.Model):
	degree = models.CharField(max_length=10, unique=True)
	
class FamilyRelationshipType(models.Model):
	relationship = models.CharField(max_length=30, unique=True)

class FamilyRelationship(Timestamped):
	person1 = models.ForeignKey(GeneticAnalysis, on_delete=models.PROTECT, related_name='first')
	person2 = models.ForeignKey(GeneticAnalysis, on_delete=models.PROTECT, related_name='second')
	degree = models.ForeignKey(FamilyRelationshipDegree, on_delete=models.PROTECT)
	relationship = models.ForeignKey(FamilyRelationshipType, null=True, on_delete=models.PROTECT)
	version = models.PositiveSmallIntegerField(null=True)
	notes = models.TextField(blank=True)
