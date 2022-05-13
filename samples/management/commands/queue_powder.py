from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from samples.models import Sample, PowderSample, PowderPrepQueue, ExpectedComplexity, SamplePrepProtocol

class Command(BaseCommand):
	help = 'For a sample starting as a powder, queue for wetlab prep as a powder'
	
	def add_arguments(self, parser):
		parser.add_argument('id', type=int)
		parser.add_argument('--priority', default=2, type=int)
		parser.add_argument('--expected_complexity')
		parser.add_argument('--udg', default='partial')
		parser.add_argument('-l', '--lab')
		parser.add_argument('-p', '--protocol')
		
	def handle(self, *args, **options):		
		sample = Sample.objects.get(id=options['id'])
		if options['expected_complexity']:
			expected_complexity = ExpectedComplexity.objects.get(description=options['expected_complexity'])
			sample.expected_complexity = expected_complexity
			sample.save()
		
		try:
			powder_sample = PowderSample.objects.get(sample=sample)
		except PowderSample.DoesNotExist:
			powder_sample = None
		
		try:
			queue_element = PowderPrepQueue.objects.get(sample=sample, powder_sample=powder_sample, udg_treatment=options['udg'])
			self.stdout.write('updated')
		except PowderPrepQueue.DoesNotExist:
			queue_element = PowderPrepQueue(sample=sample, powder_sample=powder_sample, udg_treatment=options['udg'], priority=options['priority'])
			self.stdout.write('created')
		
		queue_element.priority=options['priority']
		
		lab = options['lab']
		if lab:
			queue_element.sample_prep_lab = lab
			
		if options['protocol']:
			protocol = SamplePrepProtocol.objects.get(preparation_method=options['protocol'])
			queue_element.sample_prep_protocol = protocol
		queue_element.save()
		
