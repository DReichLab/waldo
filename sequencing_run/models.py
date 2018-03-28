from django.db import models

# Create your models here.
class SequencingRun(models.Model):
	illumina_directory = models.CharField(max_length=255, unique=True)
	
	def __str__(self):
		return self.illumina_directory

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
	
	sequencing_run = models.ForeignKey(SequencingRun, on_delete=models.CASCADE)
	sequencing_date = models.DateField()
	slurm_job_number = models.IntegerField(null=True)
	top_samples_to_demultiplex = models.IntegerField()
	triggering_flowcell = models.ForeignKey(Flowcell, on_delete=models.SET_NULL, null=True, related_name='triggered_analysis')
	prior_flowcells_for_analysis = models.ManyToManyField(Flowcell)
	
# a library may comprise multiple demultiplexed bams from different sequencing runs
class AnalyzedLibrary(models.Model):
	sample = models.IntegerField()
	extract = models.IntegerField()
	library = models.IntegerField()
	experiment = models.CharField(max_length=20)
	udg = models.CharField(max_length=10)
	workflow = models.CharField(max_length=100)
	report_path = models.CharField(max_length=300, blank=True)
	capture_name = models.CharField(max_length=50)
	analysis_time = models.DateTimeField("completed analysis time")

# a demultiplexed bam with no associated sample/library/extract information
class DemultiplexedSequencing(models.Model):
	flowcell = models.ForeignKey(Flowcell, on_delete=models.CASCADE)
	i5_index = models.CharField(max_length=10)
	i7_index = models.CharField(max_length=10)
	p5_barcode = models.CharField(max_length=50, blank=True)
	p7_barcode = models.CharField(max_length=50, blank=True)
	reference = models.CharField(max_length=30)
	path = models.CharField(max_length=300)
	analyzed_library = models.ForeignKey(AnalyzedLibrary, on_delete=models.SET_NULL, null=True)
	
	class Meta:
		unique_together = (("flowcell", "p5_barcode", "p7_barcode", "i5_index", "i7_index", "reference"),)
	


