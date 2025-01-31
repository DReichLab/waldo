from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

import re

from samples.models import Extract, Library, sample_re, lysate_re, extract_re
	

class Command(BaseCommand):
	help = "Check that extract number matches extract ID. Prints extract PK, extract number, and extract ID string for mismatches."
	
	def add_arguments(self, parser):
		parser.add_argument('ids', help='show extract IDs only', nargs='*')
		parser.add_argument('--id_only', help='show extract IDs only', action='store_true')
		
	def handle(self, *args, **options):
		compiled_extract_re = re.compile(sample_re + lysate_re + extract_re[:-1]) # remove trailing ? to force extract section to appear
		compiled_control_re = re.compile(r'control_(library|extract)_[a-zA-Z\d._]*(?:\.E(?P<extract>[\d]+))')
		
		if len(options['ids']) > 0:
			query_set = Extract.objects.filter(extract_id__in=options['ids'])
		else:
			query_set = Extract.objects.all()
		for extract in query_set:
			checked = False
			# extract number in extract ID
			match = re.match(compiled_extract_re, extract.extract_id)
			if match: # parses with regex
				# check that this matches extract number
				number_from_str = int(match.groupdict()['extract'])
				if extract.reich_lab_extract_number == number_from_str:
					checked = True
			else:
				match = re.match(compiled_control_re, extract.extract_id)
				if match: # parses with regex
					# check that this matches extract number
					number_from_str = int(match.groupdict()['extract'])
					if extract.reich_lab_extract_number == number_from_str:
						checked = True
				
			if not checked:
				outputs = [extract.extract_id]
				if not options['id_only']:
					outputs = [str(extract.id), str(extract.reich_lab_extract_number), extract.extract_batch.batch_name] + outputs
				self.stdout.write('\t'.join(outputs))
