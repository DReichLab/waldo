from django.core.management.base import BaseCommand, CommandError
from samples.models import ExtractionBatch, WetLabStaff

import re

class Command(BaseCommand):
	help = 'Add lysates identified by Reich Lab library id to a shotgun or capture plate. This plate must already exist.'
	
	def add_arguments(self, parser):
		parser.add_argument('user')
		parser.add_argument("extract_batch_name")
		
	def handle(self, *args, **options):
		plate = ExtractionBatch.objects.get(batch_name=options['extract_batch_name'])
		
		# This needs enhancement if there are duplicate names
		name = options['user']
		wetlab_user = WetLabStaff.objects.get(first_name=name)
		user = wetlab_user.login_user
		
		plate.rotate(user)
