#!/usr/bin/python

import subprocess
import sys

def ssh_command(host, command, output_std=False, output_error=False):
	ssh_result = subprocess.Popen(["ssh", "%s" % host, command],
						shell=False,
						stdout=subprocess.PIPE,
						stderr=subprocess.PIPE,
						universal_newlines=True)
	
	if output_std:
		lines = ssh_result.stdout.readlines()
		for line in lines:
			print (line)
			
	if output_error:
		lines = ssh_result.stderr.readlines()
		for line in lines:
			sys.stderr.write (line)
	
	return ssh_result
