from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db import transaction
from samples.models import DataInstance, get_sample_by_anyid, DataFileAssignment
from sequencing_run.models import GeneticAnalysis, FamilyRelationship
from django.db.models import Q

class Command(BaseCommand):
	help = 'Inspect data instances by sample'
	
	def add_arguments(self, parser):
		parser.add_argument('samples', nargs='*')
		parser.add_argument('--delete_orphans', action='store_true')
		
	def handle(self, *args, **options):
		samples = options['samples']
		
		for sample_str in samples:
			sample = get_sample_by_anyid(sample_str)
			data_instances = DataInstance.objects.filter(primary_sample=sample)
			for instance in data_instances:
				self.stdout.write(str(instance))
				
		if options['delete_orphans']:
			with transaction.atomic():
				for data_instance in DataInstance.objects.all():
					analyses = GeneticAnalysis.objects.filter(data_instance=data_instance)
					relationships = FamilyRelationship.objects.filter(Q(person1=data_instance) | Q(person2=data_instance))
					if analyses.count() == 0 and relationships.count() == 0: # DataInstance is not used, so delete it
						assignments = DataFileAssignment.objects.filter(collection=data_instance)
						assignments.delete()
						self.stderr.write(f'Deleting {data_instance.id}')
						data_instance.delete()
