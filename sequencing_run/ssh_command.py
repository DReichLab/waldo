#!/usr/bin/python

from __future__ import print_function
import subprocess
import sys

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
