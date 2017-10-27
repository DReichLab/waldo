#!/usr/bin/python

import subprocess
import sys

def ssh_command(host, command, output_std=False, output_error=False):
	ssh_result = subprocess.Popen(["ssh", "%s" % host, command],
						shell=False,
						stdout=subprocess.PIPE,
						stderr=subprocess.PIPE)
	
	if output_std:
		lines = ssh_result.stdout.readlines()
		for line in lines:
			print (line.decode('utf-8'))
			
	if output_error:
		lines = ssh_result.stderr.readlines()
		for line in lines:
			sys.stderr.write (line.decode('utf-8'))
	
	return ssh_result
