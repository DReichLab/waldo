from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db import transaction
from samples.models import Sample, PowderSample, PowderPrepQueue, ExpectedComplexity, SamplePrepProtocol

def reich_lab_sample_num(s):
	if s.startswith('S'):
		s = s[1:]
	return int(s)

class Command(BaseCommand):
	help = 'For a sample starting as a powder, queue for wetlab prep as a powder'
	
	def add_arguments(self, parser):
		parser.add_argument('-s', '--sample', nargs='+', help='Reich lab sample ids', default=[])
		parser.add_argument('--pk', nargs='+', help='For samples staring from primary key (not the Reich lab sample id number)', type=int, default=[])
		parser.add_argument('--priority', default=2, type=int)
		parser.add_argument('--expected_complexity')
		parser.add_argument('--udg', default='partial')
		parser.add_argument('-l', '--lab')
		parser.add_argument('-p', '--protocol')
		
	def handle(self, *args, **options):
		# assemble set
		
		samples_from_reich_lab_id = Sample.objects.filter(reich_lab_id__in=[reich_lab_sample_num(s) for s in options['sample']])
		samples_from_pk = Sample.objects.filter(id__in=options['pk'])
		samples = samples_from_reich_lab_id | samples_from_pk
		
		with transaction.atomic():
			for sample in samples:
				if options['expected_complexity']:
					expected_complexity = ExpectedComplexity.objects.get(description=options['expected_complexity'])
					sample.expected_complexity = expected_complexity
					sample.save()
				
				powder_sample = PowderSample.objects.get(sample=sample)
				
				# Not sure whether we need to be able to queue multiple copies
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
		
