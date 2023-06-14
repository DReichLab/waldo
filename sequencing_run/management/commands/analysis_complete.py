from django.core.management.base import BaseCommand, CommandError
from django.core.mail import send_mail
from django.conf import settings
import datetime
from sequencing_run.models import SequencingAnalysisRun

def send_notification_mail(email_addresses, name, date_string):
	send_mail(
		f"{date_string}_{name} completed analysis",
		f"This is an automated message from WALDO that sequencing data for {date_string}_{name} has completed analysis.",
		"waldo.noreply",
		email_addresses,
		fail_silently=False,
	)

class Command(BaseCommand):
	help = 'signal that analysis is finished, recording state for web interface and sending notification email'
	
	def add_arguments(self, parser):
		parser.add_argument('--date_string')
		parser.add_argument('--name')
		parser.add_argument('-f', '--force', action='store_true')
		
	def handle(self, *args, **options):
		date_string = options['date_string']
		name = options['name']
		date = datetime.datetime.strptime(date_string, "%Y%m%d").date()
		
		analysis_run = SequencingAnalysisRun.objects.get(name=name, sequencing_date=date)
		if analysis_run.processing_state != SequencingAnalysisRun.FINISHED or options['force']:
			analysis_run.processing_state = SequencingAnalysisRun.FINISHED
			analysis_run.save()
			send_notification_mail(settings.EMAILS_ANALYSIS_COMPLETE, name, date_string)
