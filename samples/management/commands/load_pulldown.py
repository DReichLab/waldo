from django.core.management.base import BaseCommand, CommandError
from samples.pipeline import load_pulldown_stdout, load_pulldown_dblist, test_results_exist

class Command(BaseCommand):
	help = 'Load a pulldown stdout output and dblist input to database'
	
	def add_arguments(self, parser):
		parser.add_argument('-l', '--release_version_label', required=True)
		parser.add_argument('-n', '--sequencing_run_name', required=True)
		parser.add_argument('-s', '--split_lane_file', help="map of libraries to split lane seq run lanes", default=None)
		parser.add_argument('--dblist', required=True)
		parser.add_argument('-p', '--pulldown', help='filenames for stdout for normal (non-damage-restricted) pulldowns', nargs='*')
		parser.add_argument('-d', '--damage_restricted', help='filenames for stdout for damage-restricted pulldowns', nargs='*')
		parser.add_argument('-t', '--test_only', help='test for results existence only', action='store_true')
		
	def handle(self, *args, **options):
		pulldown = options['pulldown']
		dblist = options['dblist']
		release_version_label = options['release_version_label']
		sequencing_run_name = options['sequencing_run_name']
		damage_restricted = options['damage_restricted']
		split_lane = options['split_lane_file']

		if split_lane:
			split_lane_map = {}
			lines = open(split_lane, 'r').readlines()
			for line in lines:
				fields = line.split()
				lib_id = fields[0]
				split_lane_seq_name = fields[-1]
				split_lane_map[lib_id] = split_lane_seq_name
		else:
			split_lane_map = None
		
		if options['test_only']:
			for p in pulldown:
				test_results_exist(p, sequencing_run_name)
		else:
			for p in pulldown:
				load_pulldown_stdout(p, release_version_label, sequencing_run_name, False, split_lane_map)
			for p in damage_restricted:
				load_pulldown_stdout(p, release_version_label, sequencing_run_name, True, split_lane_map)
			load_pulldown_dblist(dblist, release_version_label, sequencing_run_name, split_lane_map)
