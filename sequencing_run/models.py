from django.db import models

# Create your models here.
class SequencingRun(models.Model):
	illumina_directory = models.CharField(max_length=255, unique=True)
	
	def __str__(self):
		return self.illumina_directory

class SequencingScreeningAnalysisRun(models.Model):
	STARTED = 0
	COPYING_SEQUENCING_DATA = 1
	PREPARING_JSON_INPUTS = 2
	PREPARING_RUN_SCRIPT = 3
	RUNNING_SCREENING_ANALYSIS = 4
	FINISHED = 5
	FAILED = -1
	
	ANALYSIS_RUN_STATES = (
		(STARTED, 'not started'),
		(COPYING_SEQUENCING_DATA, 'copying sequencing data to Orchestra/O2'),
		(PREPARING_JSON_INPUTS, 'preparing json inputs'),
		(PREPARING_RUN_SCRIPT, 'preparing run script'),
		(RUNNING_SCREENING_ANALYSIS, 'running screening analysis'),
		(FINISHED, 'finished'),
		(FAILED, 'failed')
	)
	
	name = models.CharField("sequencing run name", max_length=100)
	start = models.DateTimeField("sequencing run processing run start time")
	stop = models.DateTimeField("sequencing run processing run stop time", null=True)
	processing_state = models.IntegerField(default=0, choices=ANALYSIS_RUN_STATES)
	
	sequencing_run = models.ForeignKey(SequencingRun, on_delete=models.CASCADE)
	sequencing_date = models.DateField()
	slurm_job_number = models.IntegerField(null=True)
	top_samples_to_demultiplex = models.IntegerField()
