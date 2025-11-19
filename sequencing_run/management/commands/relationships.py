from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db import transaction
from django.db.models import Count, Q

from pathlib import Path
import re

from samples.models import get_sample_by_anyid
from sequencing_run.models import FamilyRelationship

class Command(BaseCommand):
	help = 'Find relationships for an individual' 
	
	def add_arguments(self, parser):
		parser.add_argument('ids', nargs='+', help='Individual IDs')
		parser.add_argument('--max_degree', type=float)
		parser.add_argument('--delete', action='store_true')
		
	def handle(self, *args, **options):
		max_degree = options['max_degree'] if options['max_degree'] is not None else None
		
		with transaction.atomic():
			for individual_id in options['ids']:
				sample = get_sample_by_anyid(individual_id)
				relations = FamilyRelationship.objects.filter(Q(person1__primary_sample=sample) | Q(person2__primary_sample=sample)).order_by('degree')
				if max_degree is not None:
					relationships = relationships.filter(degree__lte=max_degree)
				for relation in relations:
					self.stdout.write(str(relation))
					if options['delete']:
						relation.delete()
