from sequencing_run.ssh_command import ssh_command
from sequencing_run.models import SequencingRun, SequencingScreeningAnalysisRun
import os
import re

from django.utils import timezone

def start_screening_analysis(source_illumina_dir, sequencing_run_name, sequencing_date, number_top_samples_to_demultiplex):
	date_string = sequencing_date.strftime('%Y%m%d')
	destination_directory = date_string + '_' + sequencing_run_name
	
	scratch_illumina_directory = "/n/scratch2/mym11/automated_pipeline/" + destination_directory
	
	run_entry = SequencingScreeningAnalysisRun(
		name = sequencing_run_name, 
		start = timezone.now(),
		processing_state = SequencingScreeningAnalysisRun.STARTED,
		sequencing_run = SequencingRun.objects.get(illumina_directory=source_illumina_dir),
		sequencing_date = sequencing_date,
		top_samples_to_demultiplex = number_top_samples_to_demultiplex
	)
	run_entry.save()
		
	# copy illumina directory
	#copy_illumina_directory(source_illumina_dir, destination_directory)
	run_entry.processing_state = SequencingScreeningAnalysisRun.COPYING_SEQUENCING_DATA
	run_entry.save()
	# generate json input file
	replace_parameters('template.json', scratch_illumina_directory, sequencing_run_name, date_string, number_top_samples_to_demultiplex)
	run_entry.processing_state = SequencingScreeningAnalysisRun.PREPARING_JSON_INPUTS
	run_entry.save()
	# generate SLURM script
	# TODO replace test with template
	replace_parameters('test.sh', scratch_illumina_directory, sequencing_run_name, date_string, number_top_samples_to_demultiplex)
	run_entry.processing_state = SequencingScreeningAnalysisRun.PREPARING_RUN_SCRIPT
	run_entry.save()
	# make directory
	
	# start job
	start_result = start_cromwell(date_string, sequencing_run_name)
	run_entry.processing_state = SequencingScreeningAnalysisRun.RUNNING_SCREENING_ANALYSIS
	# retrieve SLURM job number from output
	for line in start_result.stdout.readlines():
		line = line.decode('utf-8')
		print(line)
		m = re.match('Submitted batch job[\s]+(\d+)', line)
		if m is not None:
			run_entry.slurm_job_number = int(m.group(1))
			
	run_entry.save()
	
# Sequencing data is stored on the HMS Genetics filesystem.
# This needs to be copied to the research computing O2 cluster
# before analysis can begin
def copy_illumina_directory(source_illumina_dir, scratch_illumina_directory):
	host = "mym11@transfer.rc.hms.harvard.edu"
	command = "rsync -a /files/Genetics/reichseq/reich/reichseq/reich/" + source_illumina_dir + " " + scratch_illumina_directory
	ssh_result = ssh_command(host, command, True, True)
	return ssh_result

#values passed to construct the command string are sanitized by form validation
def replace_parameters(source_filename, scratch_illumina_directory, run_name, date_string, num_samples):
	escaped_scratch_illumina_directory = scratch_illumina_directory.replace('/','\\/')
	extension = os.path.splitext(source_filename)[1]
	host = "mym11@login.rc.hms.harvard.edu"	
	command = "sed '" \
		+ "s/INPUT_LABEL/" + run_name + "/;" \
		+ "s/INPUT_DATE/" + date_string + "/;" \
		+ "s/INPUT_DIRECTORY/" + escaped_scratch_illumina_directory + "/;" \
		+ "s/INPUT_NUM_SAMPLES/" + str(num_samples) + "/" \
		+ "'" \
		+ " /home/mym11/pipeline/run/" + source_filename \
		+ " > /home/mym11/pipeline/run/" + date_string + "_" + run_name + extension
	ssh_result = ssh_command(host, command, True, True)
	return ssh_result

def start_cromwell(date_string, run_name):
	host = "mym11@login.rc.hms.harvard.edu"
	command = "sbatch /home/mym11/pipeline/run/" + date_string + "_" + run_name + ".sh"
	ssh_result = ssh_command(host, command, False, True) # stdout printing is False to preserve SLURM job number output
	return ssh_result
