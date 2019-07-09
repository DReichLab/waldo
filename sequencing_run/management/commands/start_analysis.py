from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.utils import timezone
import datetime
from sequencing_run.analysis import start_analysis, single_indices_only
from sequencing_run.models import SequencingRun
from sequencing_run.ssh_command import ssh_command

class Command(BaseCommand):
	help = 'start an analysis from the command line, optionally skipping copy of the illumina directory (assumed manual external copy)'
	
	def add_arguments(self, parser):
		parser.add_argument('--date_string', required=True)
		parser.add_argument('--name', nargs='+', required=True)
		parser.add_argument('--illumina_directory', required=True)
		parser.add_argument('--create_illumina_entry', action='store_true', help='Create the database entry for the illumina directory. Use this for when data are not in the reichseq/reich NextSeq location. Implies skip_copy as well.')
		parser.add_argument('--demultiplex', type=int, default=150)
		parser.add_argument('--skip_copy', action='store_false')
		parser.add_argument('--hold', action='store_true')
		parser.add_argument('--allow_new_sequencing_run_id', action='store_true')
		parser.add_argument('--broad', action='store_true')
		parser.add_argument('--broad_shotgun', action='store_true')
		parser.add_argument('--i5', action='store_true')
		parser.add_argument('--i7', action='store_true')
		parser.add_argument('--library_id', nargs='*')
		parser.add_argument('--query_name', help='This is the sequencing_id under which the indices are stored in sequenced_library')
		
	def handle(self, *args, **options):
		date_string = options['date_string']
		sequencing_run_names = options['name']
		sequencing_date = datetime.datetime.strptime(date_string, "%Y%m%d").date()
		source_illumina_dir = options['illumina_directory']
		create_illumina_entry = options['create_illumina_entry']
		number_top_samples_to_demultiplex = options['demultiplex']
		copy = options['skip_copy'] and not create_illumina_entry
		hold = options['hold']
		allow_new_sequencing_run_id = options['allow_new_sequencing_run_id']
		
		combined_sequencing_run_name = '_'.join(sequencing_run_names)
		
		is_broad_shotgun = options['broad_shotgun']
		is_broad = options['broad'] or options['broad_shotgun']
		if is_broad_shotgun: # link demultiplex directory
			directory = '{}_{}'.format(date_string, combined_sequencing_run_name)
			command = 'ln -s {0}/{2} {1}/{2}'.format(settings.DEMULTIPLEXED_BROAD_SHOTGUN_PARENT_DIRECTORY, settings.DEMULTIPLEXED_PARENT_DIRECTORY, directory)
			ssh_result = ssh_command(settings.COMMAND_HOST, command, True, True)
		
		library_ids = options['library_id']
		# read I5 and I7 indices from Zhao's MySQL database
		query_name = None
		if library_ids is not None and len(library_ids) == 1:
			query_name = [options['query_name']]
			i5, i7 = single_indices_only(query_name, library_ids[0]) 
		
		additional_replacements = {}
		if options['i5']:
			additional_replacements['I5_INDEX'] = i5
		if options['i7']:
			additional_replacements['I7_INDEX'] = i7
		
		if create_illumina_entry:
			seq_run, created = SequencingRun.objects.get_or_create(illumina_directory=source_illumina_dir)
		
		start_analysis(source_illumina_dir, combined_sequencing_run_name, sequencing_date, number_top_samples_to_demultiplex, sequencing_run_names, copy, hold, allow_new_sequencing_run_id, is_broad, library_ids, additional_replacements, query_name)
