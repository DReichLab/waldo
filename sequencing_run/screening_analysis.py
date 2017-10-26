from sequencing_run.ssh_command import ssh_command
import os

def start_screening_analysis(source_illumina_dir, sequencing_run_name, sequencing_date, number_top_samples_to_demultiplex):
	date_string = sequencing_date.strftime('%Y%m%d')
	destination_directory = date_string + '_' + sequencing_run_name
	print (source_illumina_dir)
	print (sequencing_run_name)
	print (date_string)
	print (number_top_samples_to_demultiplex)
	print (destination_directory)
	
	scratch_illumina_directory = "/n/scratch2/mym11/automated_pipeline/" + destination_directory
	
	run_entry = SequencingScreeningAnalysisRun()
		
	# copy illumina directory
	#copy_illumina_directory(source_illumina_dir, destination_directory)
	# generate json input file
	#replace_parameters('template.json', scratch_illumina_directory, sequencing_run_name, date_string, number_top_samples_to_demultiplex)
	# generate SLURM script
	#replace_parameters('template.sh', scratch_illumina_directory, sequencing_run_name, date_string, number_top_samples_to_demultiplex)
	# start job
	#start_cromwell(date_string, run_name)
	
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
	extension = os.path.splitext(source_filename)[1]
	host = "mym11@login.rc.hms.harvard.edu"
	command = "sed '" \
		+ "s/INPUT_LABEL/" + run_name + "/;" \
		+ "s/INPUT_DATE/" + date_string + "/;" \
		+ "s/INPUT_DIRECTORY/" + scratch_illumina_directory + "/;" \
		+ "s/INPUT_NUM_SAMPLES/" + num_samples + "/" \
		+ "'" \
		+ " /home/mym11/pipeline/run/" + source_filename \
		+ " > /home/mym11/pipeline/run/" + date_string + "_" + run_name + extension
	ssh_result = ssh_command(host, command, True, True)
	return ssh_result

def start_cromwell(date_string, run_name):
	host = "mym11@login.rc.hms.harvard.edu"
	command = "sbatch /home/mym11/pipeline/run/" + date_string + "_" + run_name + ".sh"
	ssh_result = ssh_command(host, command, True, True)
	return ssh_result
