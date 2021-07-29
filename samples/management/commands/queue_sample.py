from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from samples.models import Sample, SamplePrepQueue, ExpectedComplexity, SamplePrepProtocol

class Command(BaseCommand):
	help = 'Queue a sample for wetlab prep by queue ID'
	
	def add_arguments(self, parser):
		parser.add_argument('queue_id')
		parser.add_argument('--priority', default=200, type=int)
		parser.add_argument('--expected_complexity', default='high')
		parser.add_argument('--sample_prep_protocol')
		parser.add_argument('--udg', default='partial')
		
	def handle(self, *args, **options):		
		sample = Sample.objects.get(queue_id=options['queue_id'])
		expected_complexity = ExpectedComplexity.objects.get(description=options['expected_complexity'])
		
		if options['sample_prep_protocol']:
			sample_prep_protocol = SamplePrepProtocol.objects.get(preparation_method=options['sample_prep_protocol'])
		else:
			sample_prep_protocol = None
		
		try:
			queue_element = SamplePrepQueue.objects.get(sample=sample, sample_prep_protocol=sample_prep_protocol, udg_treatment=options['udg'])
			self.stdout.write('updated')
		except SamplePrepQueue.DoesNotExist:
			queue_element = SamplePrepQueue.objects.create(sample=sample, sample_prep_protocol=sample_prep_protocol, udg_treatment=options['udg'], priority=options['priority'])
			self.stdout.write('created')
		
		queue_element.priority=options['priority']
		queue_element.expected_complexity = expected_complexity
		queue_element.save()
		
