from django.core.management.base import BaseCommand, CommandError
from samples.models import WetLabStaff
from samples.sequencing_run_partial import create_sequencing_run_four_series

class Command(BaseCommand):
	help = "Create multiple sequencing runs from indexed library plates (capture or shotgun) based on column plate position."
	
	def add_arguments(self, parser):
		parser.add_argument("--capture_names", required=True, nargs='+', help='Indexed library plates to add to sequencing run')
		parser.add_argument("--sequencing_run", required=True, help='Sequencing run base name. Appended will be _#_SQ')
		parser.add_argument('--user', required=True, help='Wetlab user first name')
		
	def handle(self, *args, **options):
		name = options['user']
		wetlab_user = WetLabStaff.objects.get(first_name=name)
		user = wetlab_user.login_user

		create_sequencing_run_four_series(options['capture_names'], options['sequencing_run'], user)
