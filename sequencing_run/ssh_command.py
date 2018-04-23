#!/usr/bin/python

from __future__ import print_function
import subprocess
import sys
import tempfile
import os

from django.conf import settings

def ssh_command(host, command, output_std=None, output_error=None):
	ssh_result = subprocess.Popen(["ssh", "%s" % host, command],
						shell=False,
						stdout=subprocess.PIPE,
						stderr=subprocess.PIPE,
						universal_newlines=True)
	
	if output_std:
		output = sys.stdout if output_std == True else output_std
		lines = ssh_result.stdout.readlines()
		for line in lines:
			print (line.strip(), file=output)
			
	if output_error:
		output = sys.stderr if output_error == True else output_error
		lines = ssh_result.stderr.readlines()
		for line in lines:
			print (line.strip(), file=output)
	
	return ssh_result

# put a file in the run directory with the requested contents
def save_file_with_contents(contents, sequencing_date_string, sequencing_run_name, extension, host):
	# using echo limits the file size
	# save a temporary local file using a temporary directory, then copy this to run directory
	with tempfile.TemporaryDirectory() as temp_directory:
		filename = "{}_{}.{}".format(sequencing_date_string, sequencing_run_name, extension)
		filename_full_path = os.path.join(temp_directory, filename)
		with open(filename_full_path, 'w') as f:
			f.write(contents)
		destination = "{0}:{1}/{2}_{3}/{2}_{3}.{4}".format(host, settings.RUN_FILES_DIRECTORY, sequencing_date_string, sequencing_run_name, extension)
		subprocess.check_output(['scp', filename_full_path, destination])
