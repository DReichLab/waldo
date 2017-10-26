from sequencing_run.ssh_command import ssh_command 

# acquire list of SLURM jobs that are running tied to a known sequencing run
def query_job_status():
	host = "mym11@login.rc.hms.harvard.edu"
	command = 'squeue -u mym11 -o "%.18i %.9P %.45j %.8u %.8T %.10M %.9l %.6D %.3C %R"'
	ssh_result = ssh_command(host, command)
