from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

import argparse

from samples.models import Sample, get_sample_by_anyid, get_wetlab_staff

class Command(BaseCommand):
	help = "Copy a sample. Used for example, when a sample merge has two samples, but they both need to be present for family relationship entries."
	
	def add_arguments(self, parser):
		parser.add_argument('-s', '--sample', required=True, help='sample to copy')
		parser.add_argument('-r', '--reich_lab_id', type=int, help='Reich lab ID to assign')
		parser.add_argument('-e', '--external', help='external ID to assign')
		parser.add_argument('-u', '--user', nargs='+', required=True, help='wetlab user for save accounting')
		
	def handle(self, *args, **options):
		wetlab_user = get_wetlab_staff(options['user'])
		#self.stdout.write(f'User: {wetlab_user.name()}')
		user = wetlab_user.login_user
		
		sample = get_sample_by_anyid(options['sample'])
		reich_lab_id = options['reich_lab_id']
		external_id = options['external']
		if reich_lab_id or external_id:
			sample.pk = None
			if reich_lab_id:
				sample.reich_lab_id = reich_lab_id
			if external_id:
				sample.external_id = reich_lab_id
			sample.save(save_user=user)
		else:
			self.stderr.write('Need either a reich_lab_id or an external id')
	
