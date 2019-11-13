from django.db import models

from samples.models import Timestamped

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

class Capture(models.Model):
	name = models.CharField(max_length=50, unique=True)
	
class Batch(models.Model):
	name = models.CharField(max_length=50, unique=True)

class Library(models.Model):
	experiment = models.CharField(max_length=20)
	udg = models.CharField(max_length=10)
	workflow = models.CharField(max_length=100)
	reference = models.CharField(max_length=30)
	path = models.CharField(max_length=300)
	release_time = models.DateTimeField("release time", auto_now_add=True)
	version = models.IntegerField()
	capture = models.ForeignKey(Capture, on_delete=models.PROTECT)
	batch = models.ForeignKey(Batch, on_delete=models.PROTECT)
	
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
	p5_barcode = models.CharField(max_length=10, blank=True)
	p7_barcode = models.CharField(max_length=10, blank=True)
	reference = models.CharField(max_length=30)
	path = models.CharField(max_length=300)
	library = models.ManyToManyField(ReleasedLibrary) # this needs to be many-to-many to support versions
	

class MTAnalysis(Timestamped):
	demultiplexing_sequences = models.BigIntegerField()
	sequences_passing_filters = models.BigIntegerField()
	sequences_aligning = models.BigIntegerField()
	sequences_aligning_post_dedup = models.BigIntegerField()
	coverage = models.FloatField()
	mean_median_sequence_length = models.FloatField()
	damage_last_base = models.FloatField()
	consensus_match = models.FloatField()
	consensus_match_95ci = models.FloatField()
	haplogroup = models.CharField(max_length=25)
	haplogroup_confidence = models.FloatField()
	
class SpikeAnalysis(Timestamped):
	bioinfo_processing_protocol = models.CharField(max_length=50)
	spike_track_id = models.CharField(max_length=50)
	spike_pre_aut = models.IntegerField()
	spike_post_aut = models.IntegerField()
	spike_post_y = models.IntegerField()
	spike_complexity = models.FloatField()
	spike_sex = models.CharField(max_length=10)
	screening_outcome = models.CharField(max_length=50)

class ShotgunAnalysis(Timestamped):
	bioinfo_processing_protocol = models.CharField(max_length=50)
	track_id = models.CharField(max_length=50)
	raw_sequences = models.BigIntegerField()
	sequences_passing_filters = models.BigIntegerField()
	reads_mapped_hg19 = models.BigIntegerField()
	mean_median_sequence_length = models.FloatField()
	percent_hg19 = models.FloatField()
	damage_rate = models.FloatField()
	fraction_hg19_hit_mtdna = models.FloatField()
	
class NuclearAnalysis(Timestamped):
	bioinfo_processing_protocol = models.CharField(max_length=50)
	pulldown_logfile_location = models.CharField(max_length=300)
	pulldown_1st_column_nickdb = models.CharField(max_length=50)
	pulldown_2nd_column_nickdb_alt_sample = models.CharField(max_length=150)
	pulldown_3rd_column_nickdb_bam = models.CharField(max_length=300)
	pulldown_4th_column_nickdb_hetfa = models.CharField(max_length=500)
	pulldown_5th_column_nickdb_readgroup_diploid_source = models.TextField()
	seq_run_file_name = models.CharField(max_length=150) # TODO no idea what this is
	track_id_report_file = models.CharField(max_length=100)
	raw_reads_or_deindexing = models.BigIntegerField()
	sequences_merge_pass_barcode = models.BigIntegerField()
	target_sequences_pass_qc_predup = models.BigIntegerField()
	target_sequences_pass_qc_postdedup = models.BigIntegerField()
	unique_targets_hit = models.IntegerField()
	unique_snps_hit = models.IntegerField()
	coverage_targeted_positions = models.FloatField()
	expected_coverage_10_marginal_uniqueness = models.FloatField()
	expected_coverage_37_marginal_uniqueness = models.FloatField()
	mean_median_seq_length = models.FloatField()
	damage_last_base = models.FloatField()
	x_hits = models.IntegerField()
	y_hits = models.IntegerField()
	sex = models.CharField(max_length=20)
	y_haplogroup = models.CharField(max_length=20)
	angsd_snps = models.IntegerField()
	angsd_mean = models.FloatField()
	angsd_z = models.FloatField()
	assessment = models.CharField(max_length=250)
	version_release = models.CharField(max_length=10)
	results_note = models.TextField()
	find = models.TextField()
