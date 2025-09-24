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
		parser.add_argument('-q', '--quiet', action='store_true', help='Do not print each instance')
		parser.add_argument('-k', '--compare_from_sample', action='store_true', help='compare data instances as specified by samples')
		parser.add_argument('--delete_duplicates', action='store_true', help='For samples, if they have duplicate DataInstances, remove the duplicate with higher id')
		parser.add_argument('--delete_orphans', action='store_true')
		parser.add_argument('-c', '--compare', type=int, nargs=2, help='compare two data instances by pk to see difference')
		
	def handle(self, *args, **options):
		samples = options['samples']
		with transaction.atomic():
		
			for sample_str in samples:
				sample = get_sample_by_anyid(sample_str)
				data_instances = DataInstance.objects.filter(primary_sample=sample).order_by('id')
				for instance in data_instances:
					if not options['quiet']:
						self.stdout.write(f'{instance.id} {str(instance)}')
				if options['compare_from_sample']:
					for index1, x in enumerate(data_instances):
						for index2, y in enumerate(data_instances):
							if index2 > index1:
								self.stdout.write(f'{index2} {index1}')
								self.comparison_print(x, y)
								if options['delete_duplicates']:
									equal, in_x_not_y, in_y_not_x, lib_match = x.compare(y)
									if equal:
										self.stdout.write(f'Deleting {y.id}')
										analyses = GeneticAnalysis.objects.filter(data_instance=y)
										for analysis in analyses:
											analysis.data_instance = x
											analysis.save()
										relationships = FamilyRelationship.objects.filter(Q(person1=y) | Q(person2=y))
										for relationship in relationships:
											if relationship.person1 == y:
												relationship.person1 = x
											if relationship.person2 == y:
												relationship.person2 = x
											relationship.save()
										y.delete()
					
			if options['delete_orphans']:
				for data_instance in DataInstance.objects.all():
					analyses = GeneticAnalysis.objects.filter(data_instance=data_instance)
					relationships = FamilyRelationship.objects.filter(Q(person1=data_instance) | Q(person2=data_instance))
					if analyses.count() == 0 and relationships.count() == 0: # DataInstance is not used, so delete it
						assignments = DataFileAssignment.objects.filter(collection=data_instance)
						assignments.delete()
						self.stderr.write(f'Deleting {data_instance.id}')
						data_instance.delete()
							
			if options['compare']:
				to_compare = options['compare']
				x = DataInstance.objects.get(id=to_compare[0])
				y = DataInstance.objects.get(id=to_compare[1])
				self.comparison_print(x, y)
			
	def comparison_print(self, x, y):
			equal, in_x_not_y, in_y_not_x, lib_match = x.compare(y)
			if equal:
				self.stdout.write('equal')
			else:
				self.stdout.write('In first, not second')
				for s in in_x_not_y:
					self.stdout.write(str(s))
				self.stdout.write('In second, not first')
				for s in in_y_not_x:
					self.stdout.write(str(s))
				self.stdout.write(f'libraries match: {lib_match}')
