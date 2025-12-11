from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db import transaction
from samples.models import get_sample_by_anyid, DataInstance, data_instance_get
from django.db.models import Q

class Command(BaseCommand):
	help = 'Inspect data instances by sample'
	
	def add_arguments(self, parser):
		parser.add_argument('-s', '--sample', required=True)
		parser.add_argument('--nuclear_bam', help='Nuclear bam path', required=True)
		parser.add_argument('--nuclear_rg', nargs='+', help='Nuclear bam read groups')
		parser.add_argument('--mt_bam', help='MT bam path')
		parser.add_argument('--mt_rg', nargs='+', help='MT bam read groups')
		parser.add_argument('--libraries', nargs='+', help='libraries')
		parser.add_argument('--exact', action='store_true', help='Data files and read groups must all match. Libraries are not included in exactness.')
		
	def handle(self, *args, **options):
		with transaction.atomic():
			sample = get_sample_by_anyid(options['sample'])
			if options['libraries'] and len(options['libraries']) > 0:
				libraries = ' '.join(options['libraries'])
			else:
				libraries = None
			data_instance = data_instance_get(sample, options['nuclear_bam'], options['nuclear_rg'], options['mt_bam'], options['mt_rg'], libraries, options['exact'])
			print(data_instance)
			transaction.set_rollback(True)
