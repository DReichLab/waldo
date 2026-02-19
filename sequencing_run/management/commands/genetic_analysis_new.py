from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.contrib.auth.models import User

from samples.intake import genetic_analysis_setup
from sequencing_run.models import GeneticAnalysis

class Command(BaseCommand):
	help = 'Django command to create new genetic analysis entries. This does not suffer from web interface timeouts.' 
	
	def add_arguments(self, parser):
		parser.add_argument('new_genetic_analysis', nargs='+', help='File(s) containing new genetic analyses. Format of this file is the same as that for web upload.')
		parser.add_argument('-u', '--user', help='WALDO username, which can be non-wetlab.', required=True)
		
	def handle(self, *args, **options):
		with transaction.atomic():
			user = User.objects.get(username=options['user'])
			for filename in options['new_genetic_analysis']:
				with open(filename) as f:
					genetic_analysis_setup(f, user)
