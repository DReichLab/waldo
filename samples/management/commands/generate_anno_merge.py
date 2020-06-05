from django.core.management.base import BaseCommand, CommandError
from samples.anno import library_anno_line

class Command(BaseCommand):
	help = "Generate David's anno file for a merge file. Still requires manual rework."
	
	def add_arguments(self, parser):
		parser.add_argument('merge_list')
		
	def handle(self, *args, **options):
		merge_list_filename = options['merge_list']
		
		with open(merge_list_filename) as f:
			for line in f:
				fields = line.split()
				instance_id = fields[0]
				individual_id = fields[1]
				libraries = fields[2:]
				
				fields = library_anno_line(instance_id, None, None, libraries)
				self.stdout.write('\t'.join(fields))
