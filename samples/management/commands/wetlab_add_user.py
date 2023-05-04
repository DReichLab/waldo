from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.contrib.auth.models import User
from samples.models import WetLabStaff

class Command(BaseCommand):
	help = 'Add a wetlab user'
	
	def add_arguments(self, parser):
		parser.add_argument('-f', '--first_name', help='Wetlab user first name', required=True)
		parser.add_argument('-l', '--last_name', help='Wetlab user first name', required=True)
		parser.add_argument('-t', '--title', default='')
		parser.add_argument('-u', '--username', help='Django user login (already created from admin interface)', required=True)
		parser.add_argument('-c', '--creator', help='Django user login for user creating', required=True)
		
	def handle(self, *args, **options):
		with transaction.atomic():
			creator = User.objects.get(username=options['creator'])
			user = User.objects.get(username=options['username'])

			wetlab_user = WetLabStaff(first_name=options['first_name'], last_name=options['last_name'], title=options['title'], login_user=user)
			wetlab_user.save(save_user=creator)
