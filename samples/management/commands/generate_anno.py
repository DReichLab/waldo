from django.core.management.base import BaseCommand, CommandError
from samples.anno import library_anno_line

import sys

class Command(BaseCommand):
	help = "Generate David's anno file for a sequencing run"
	
	def add_arguments(self, parser):
		parser.add_argument('-l', '--release_version_label', required=True)
		parser.add_argument('-n', '--sequencing_run_name', required=True)
		parser.add_argument('--ind', required=True)
		
	def handle(self, *args, **options):
		release_version_label = options['release_version_label']
		sequencing_run_name = options['sequencing_run_name']
		ind_filename = options['ind']
		
		with open(ind_filename) as f:
			for line in f:
				fields = line.split()
				library_id_raw = fields[0]
				sex = fields[1]
				
				try:
					if 'Contl' in library_id_raw: # TODO also handle control entries
						print('ignoring {}'.format(library_id_raw), file=sys.stderr)
					else:
						fields = library_anno_line(library_id_raw, sequencing_run_name, release_version_label)
						self.stdout.write('\t'.join(fields))
				except Exception as e:
					print('Failure for {}'.format(library_id_raw), file=sys.stderr)
					raise e
				'''
				try:
					#self.stdout.write('\t'.join(fields))
					'\t'.join(fields)
				except:
					for i in range(len(fields)):
						if(isinstance(fields[i], float)):
							print(fields[i])
							print(i)
						#print(field)
				break
				'''
