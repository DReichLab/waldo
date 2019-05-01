from django.db import models

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
	triggering_flowcell = models.ForeignKey(Flowcell, on_delete=models.SET_NULL, null=True, related_name='triggered_analysis')
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
	flowcell = models.ForeignKey(Flowcell, on_delete=models.CASCADE, related_name='single_flowcell')
	flowcells = models.ManyToManyField(Flowcell, related_name='source_flowcells')
	i5_index = models.CharField(max_length=10)
	i7_index = models.CharField(max_length=10)
	p5_barcode = models.CharField(max_length=50, blank=True)
	p7_barcode = models.CharField(max_length=50, blank=True)
	reference = models.CharField(max_length=30)
	path = models.CharField(max_length=300)
	library = models.ManyToManyField(ReleasedLibrary) # this needs to be many-to-many to support versions
	
	class Meta:
		unique_together = (("flowcell", "p5_barcode", "p7_barcode", "i5_index", "i7_index", "reference"),)
	


