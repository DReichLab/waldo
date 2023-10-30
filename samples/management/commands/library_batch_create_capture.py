from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

import argparse, sys

from samples.models import LibraryBatch, WetLabStaff

class Command(BaseCommand):
	help = "Create a capture/raw batch from specified library batches. Use this if the batch creation from the regular interface is confused about which batches to include."
	
	def add_arguments(self, parser):
		parser.add_argument('--user', help='Wetlab user first name', required=True)
		parser.add_argument('--name', help='Capture/raw batch name', required=True)
		parser.add_argument('library_batches', nargs='+')
		
	def handle(self, *args, **options):
		library_batch_names = options['library_batches']
		starting_batch = library_batch_names[0]
		
		capture_batch_name = options['name']
		
		name = options['user']
		wetlab_user = WetLabStaff.objects.get(first_name=name)
		user = wetlab_user.login_user
		
		library_batch = LibraryBatch.objects.get(name=starting_batch)
		other_batches = LibraryBatch.objects.filter(name__in=library_batch_names[1:])
		
		library_batch.create_capture(capture_batch_name, other_batches, user)
