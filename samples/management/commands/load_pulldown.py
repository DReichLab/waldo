from django.core.management.base import BaseCommand, CommandError
from samples.pipeline import load_pulldown_stdout, load_pulldown_dblist

class Command(BaseCommand):
	help = 'Load a pulldown stdout output and dblist input to database'
	
	def add_arguments(self, parser):
		parser.add_argument('-l', '--release_version_label', required=True)
		parser.add_argument('-n', '--sequencing_run_name', required=True)
		parser.add_argument('--dblist', required=True)
		parser.add_argument('-p', '--pulldown', help='filenames for stdout for normal (non-damage-restricted) pulldowns', nargs='*')
		parser.add_argument('-d', '--damage_restricted', help='filenames for stdout for damage-restricted pulldowns', nargs='*')
		
	def handle(self, *args, **options):
		pulldown = options['pulldown']
		dblist = options['dblist']
		release_version_label = options['release_version_label']
		sequencing_run_name = options['sequencing_run_name']
		damage_restricted = options['damage_restricted']
		
		for p in pulldown:
			load_pulldown_stdout(p, release_version_label, sequencing_run_name, False)
		for p in damage_restricted:
			load_pulldown_stdout(p, release_version_label, sequencing_run_name, True)
		load_pulldown_dblist(dblist, release_version_label, sequencing_run_name)
