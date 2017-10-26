from django.db import models

# Create your models here.
class SequencingRun(models.Model):
	illumina_directory = models.CharField(max_length=255, unique=True)
	
	def __str__(self):
		return self.illumina_directory

class SequencingScreeningAnalysisRun(models.Model):
	SEQUENCING_RUN_STATES = (
		(0, 'not started'),
		(1, 'starting'),
		(2, 'copying sequencing data to Orchestra/O2'),
		(3, 'preparing run script'),
		(4, 'running screening analysis'),
		(5, 'finished'),
		(6, 'failed')
	)
	
	name = models.CharField("sequencing run name", max_length=100)
	start = models.DateTimeField("sequencing run processing run start time")
	stop = models.DateTimeField("sequencing run processing run stop time", null=True)
	processingState = models.IntegerField(default=0)
	
	sequencingRun = models.ForeignKey(SequencingRun)
	sequencing_date = models.DateField()
	slurm_job_number = models.IntegerField(null=True)
	top_samples_to_demultiplex = models.IntegerField()
