from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db import transaction

import argparse, re

from samples.models import Extract, Library, WetLabStaff, sample_re, lysate_re, extract_re

class Command(BaseCommand):
	help = "inspect extract libraries and optionally try to perform extract id fixes"
	
	def add_arguments(self, parser):
		parser.add_argument('extract', nargs='+')
		parser.add_argument('--renumber', action='store_true', help='Renumber extracts to match the extract_id string. S1234.Y1.E1')
		parser.add_argument('--rename', action='store_true', help='Replace extract ID to match extract number')
		parser.add_argument('-u', '--user', help='user to mark modifications')
		
	def handle(self, *args, **options):
		if options['renumber']:
			compiled_extract_re = re.compile(sample_re + lysate_re + extract_re[:-1]) # remove trailing ? to force extract section to appear
		user = None
		if options['user']:
			try:
				wetlab_user = WetLabStaff.objects.get(last_name=options['user'])
			except WetLabStaff.DoesNotExist:
				wetlab_user = WetLabStaff.objects.get(first_name=options['user'])
			user = wetlab_user.login_user
					
			
		with transaction.atomic():
			for extract_id in options['extract']:
				extract = Extract.objects.get(extract_id=extract_id)
				self.stdout.write(str(extract.num_libraries()))
				for library in Library.objects.filter(extract=extract).order_by('reich_lab_library_number'):
					self.stdout.write(library.reich_lab_library_id)
					if not library.reich_lab_library_id.startswith(extract_id):
						raise ValueError(f'{library.reich_lab_library_id} does not start with {extract_id}')
				self.stdout.write(str(extract.highest_library()))
				
				if options['renumber']:
					# extract number in extract ID
					match = re.match(compiled_extract_re, extract.extract_id)
					extract.reich_lab_extract_number = int(match.groupdict()['extract'])
					extract.save(save_user=user)
