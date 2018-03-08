from sequencing_run.ssh_command import ssh_command
from sequencing_run.models import SequencingRun, SequencingScreeningAnalysisRun
from sequencing_run.barcode_prep import barcodes_set, i5_set, i7_set
import os
import re

from django.utils import timezone
from django.conf import settings

def start_screening_analysis(source_illumina_dir, sequencing_run_name, sequencing_date, number_top_samples_to_demultiplex):
	date_string = sequencing_date.strftime('%Y%m%d')
	destination_directory = date_string + '_' + sequencing_run_name
	
	# the source_illumina_dir is the directory name only, not the full path
	# we need the scratch directory to include the full path including the illumina directory name for bcl2fastq in the analysis pipeline to find it
	scratch_illumina_parent_path = settings.SCRATCH_PARENT_DIRECTORY + "/" + destination_directory
	scratch_illumina_directory_path = scratch_illumina_parent_path + "/" + source_illumina_dir
	
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
	run_entry.processing_state = SequencingScreeningAnalysisRun.COPYING_SEQUENCING_DATA
	run_entry.save()
	copy_illumina_directory(source_illumina_dir, scratch_illumina_parent_path)
	# make new directory for run files
	make_run_directory(date_string, sequencing_run_name)
	# index-barcode key file
	index_barcode_keys_used(date_string, sequencing_run_name)
	# barcode and index files for run
	barcodes_set(date_string, sequencing_run_name)
	i5_set(date_string, sequencing_run_name)
	i7_set(date_string, sequencing_run_name)
	
	demultiplex_command_label = 'demultiplex'
	# generate json input file
	run_entry.processing_state = SequencingScreeningAnalysisRun.PREPARING_JSON_INPUTS
	run_entry.save()
	replace_parameters('demultiplex_template.json', scratch_illumina_directory_path, sequencing_run_name, date_string, number_top_samples_to_demultiplex, demultiplex_command_label)
	# generate SLURM script
	run_entry.processing_state = SequencingScreeningAnalysisRun.PREPARING_RUN_SCRIPT
	run_entry.save()
	replace_parameters('demultiplex_template.sh', scratch_illumina_directory_path, sequencing_run_name, date_string, number_top_samples_to_demultiplex, demultiplex_command_label)
	# start demultiplexing job
	run_entry.processing_state = SequencingScreeningAnalysisRun.RUNNING_SCREENING_ANALYSIS
	run_entry.save();
	
	start_result = start_cromwell(date_string, sequencing_run_name, demultiplex_command_label)
	# retrieve SLURM job number from output
	for line in start_result.stdout.readlines():
		print(line)
		m = re.match('Submitted batch job[\s]+(\d+)', line)
		if m is not None:
			run_entry.slurm_job_number = int(m.group(1))
	run_entry.save()
	
	# get analysis job ready, starting when demultiplexing job finishes
	analysis_command_label = 'analysis'
	replace_parameters('analysis_template.json', scratch_illumina_directory_path, sequencing_run_name, date_string, number_top_samples_to_demultiplex, analysis_command_label)
	replace_parameters('analysis_template.sh', scratch_illumina_directory_path, sequencing_run_name, date_string, number_top_samples_to_demultiplex, analysis_command_label)
	
# make new run directory
def make_run_directory(date_string, sequencing_run_name):
	command = "mkdir -p {}/{}_{}".format(settings.RUN_FILES_DIRECTORY, date_string, sequencing_run_name)
	ssh_result = ssh_command(settings.COMMAND_HOST, command, True, True)
	return ssh_result
	
# Sequencing data is stored on the HMS Genetics filesystem.
# This needs to be copied to the research computing O2 cluster
# before analysis can begin
def copy_illumina_directory(source_illumina_dir, scratch_illumina_directory):
	print(source_illumina_dir)
	print(scratch_illumina_directory)
	host = settings.TRANSFER_HOST
	command = "rsync -a {}/{} {}".format(settings.FILES_SERVER_DIRECTORY, source_illumina_dir, scratch_illumina_directory)
	ssh_result = ssh_command(host, command, True, True)
	return ssh_result

#values passed to construct the command string are sanitized by form validation
def replace_parameters(source_filename, scratch_illumina_directory, run_name, date_string, num_samples, command_label):
	escaped_scratch_illumina_directory = scratch_illumina_directory.replace('/','\\/')
	extension = os.path.splitext(source_filename)[1]
	host = settings.COMMAND_HOST
	command = "sed '" \
		+ "s/INPUT_LABEL/" + run_name + "/g;" \
		+ "s/INPUT_DATE/" + date_string + "/g;" \
		+ "s/INPUT_DIRECTORY/" + escaped_scratch_illumina_directory + "/;" \
		+ "s/INPUT_NUM_SAMPLES/" + str(num_samples) + "/" \
		+ "'" \
		+ " {}/{}".format(settings.RUN_FILES_DIRECTORY, source_filename) \
		+ " > {0}/{1}_{2}/{1}_{2}_{4}{3}".format(settings.RUN_FILES_DIRECTORY, date_string, run_name, extension, command_label)
	ssh_result = ssh_command(host, command, True, True)
	return ssh_result

# The Broad Cromwell workflow tool runs the analysis
def start_cromwell(date_string, run_name, command_label):
	host = settings.COMMAND_HOST
	command = "sbatch {0}/{1}_{2}/{1}_{2}_{3}.sh".format(settings.RUN_FILES_DIRECTORY, date_string, run_name, command_label)
	ssh_result = ssh_command(host, command, False, True) # stdout printing is False to preserve SLURM job number output
	return ssh_result

# acquire list of SLURM jobs that are running tied to a known sequencing run
def query_job_status():
	host = settings.COMMAND_HOST
	command = 'squeue -u mym11 -o "%.18i %.9P %.45j %.8u %.8T %.10M %.9l %.6D %.3C %R"'
	ssh_result = ssh_command(host, command)
	
	stdout_result = ssh_result.stdout.readlines()
	slurm_jobs_text = []
	slurm_running_jobs = []
	for line in stdout_result:
		decoded = line.strip()
		slurm_jobs_text.append(decoded) # for printing
	stderr_result = ssh_result.stderr.readlines()
	for line in stderr_result:
		decoded = line.strip()
		slurm_jobs_text.append(decoded) # for printing
		
	# iterate over running sequencing analysis runs
	# if the slurm job is not present
	expectedRunningJobs = SequencingScreeningAnalysisRun.objects.filter(processing_state=SequencingScreeningAnalysisRun.RUNNING_SCREENING_ANALYSIS)
	for expectedRunningJob in expectedRunningJobs:
		# query for sacct info and check for COMPLETED state
		#sacct -j 5790362 -o "JobID,State"
		jobID = str(expectedRunningJob.slurm_job_number)
		print ('checking SLURM job state for job ' + jobID)
		sacct_command = 'sacct -j ' + jobID + ' -o "JobID,State"'
		sacct_result = ssh_command(host, sacct_command)
		sacct_stdout = sacct_result.stdout.readlines()
		for line in sacct_stdout:			
			fields = line.split()
			#print('debugging: ', fields)
			if fields[0] == jobID:
				state = fields[1]
				if state == 'COMPLETED':
					expectedRunningJob.processing_state = SequencingScreeningAnalysisRun.FINISHED
					expectedRunningJob.save()
				if 'CANCELLED' in state or state == 'FAILED' or state == 'TIMEOUT' or state == 'NODE_FAIL':
					expectedRunningJob.processing_state = SequencingScreeningAnalysisRun.FAILED
					expectedRunningJob.save()
				
		sacct_stderr = sacct_result.stderr.readlines()
		
	return slurm_jobs_text

# get a report file from the completed analysis
def get_report_file(sequencing_date_string, sequencing_run_name, extension):
	host = settings.COMMAND_HOST
	command = 'cat ' + settings.RESULTS_PARENT_DIRECTORY + sequencing_date_string + '_' + sequencing_run_name + '/' + sequencing_date_string + '_' + sequencing_run_name + extension
	print('get_report_file ' + command)
	ssh_result = ssh_command(host, command, False, False)
	print('get_report_file fetched')
	
	# retrieve stdout from cat and return this as an array of lines
	delimiter = ''
	lines = ssh_result.stdout.readlines()
	report_output = delimiter.join(lines)
		
	return report_output

def get_final_report(sequencing_date_string, sequencing_run_name):
	return get_report_file(sequencing_date_string, sequencing_run_name, '.report')

def get_kmer_analysis(sequencing_date_string, sequencing_run_name):
	return get_report_file(sequencing_date_string, sequencing_run_name, '.kmer')

def index_barcode_keys_used(sequencing_date_string, sequencing_run_name):
	host = settings.COMMAND_HOST
	queryForKeys = 'SELECT CONCAT(p5_index, "_", p7_index, "_", p5_barcode, "_", p7_barcode), library_id, plate_id, experiment FROM sequenced_library WHERE sequencing_id="%s";' % (sequencing_run_name) ;
	command = "mysql devadna -N -e '{0}' > {1}/{2}_{3}/{2}_{3}.index_barcode_keys".format(queryForKeys, settings.RUN_FILES_DIRECTORY, sequencing_date_string, sequencing_run_name)
	ssh_command(host, command, True, True)
