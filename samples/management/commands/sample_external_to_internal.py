from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db import transaction
from samples.models import Sample, SID_IID_REGEX, get_wetlab_staff
import re

class Command(BaseCommand):
	help = 'Take a sample whose external ID should be an internal ID, remove external ID, and set internal ID'
	
	def add_arguments(self, parser):
		parser.add_argument('--ids', nargs='+', required=True)
		parser.add_argument('-u', '--user', nargs='+', required=True, help='wetlab user for save accounting')
		
	def handle(self, *args, **options):		
		wetlab_user = get_wetlab_staff(options['user'])
		self.stdout.write(f'User: {wetlab_user.name()}')
		user = wetlab_user.login_user
		with transaction.atomic():
			for sample_id in options['ids']:
				sample = Sample.objects.get(external_id=sample_id)
				sample.external_id = ''
				sample.individual_id = sample_id
				match = re.match(SID_IID_REGEX, sample_id)
				reich_lab_id = int(match.group('sample'))
				self.stdout.write(f'{reich_lab_id}')
				sample.reich_lab_id = int(match.group('sample'))
				sample.save(save_user=user)
