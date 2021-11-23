from django.core.management.base import BaseCommand
import getpass

class Command(BaseCommand):
	help = 'Simple check for username'
	
	def add_arguments(self, parser):
		pass
		
	def handle(self, *args, **options):
		self.stdout.write(getpass.getuser())
