from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db import transaction
from django.db.models import Count, Q

from pathlib import Path
import re

from samples.models import Sample, SpecialRestriction, DataFileType, DataFile, DataInstance, DataFileAssignment, PublicationLabels, Publication, SID_IID_REGEX, AssessmentCategory
from sequencing_run.models import GeneticAnalysis

def degree_to_float(s):
	degree_str = s.split('-')[0]
	if degree_str == 'Dup':
		degree = 0.0
	else:
		degree = float(degree_str)
	if '-' in s:
		degree += 0.5
	return degree
	
def genetic_id_has_file(genetic_id, filepath):
	try:
		genetic_analysis = GeneticAnalysis.objects.get(genetic_id=genetic_id)
		DataFileAssignment.objects.get(data_file__path=file1, collection=genetic_analysis.data_instance)
		return genetic_analysis
	except GeneticAnalysis.DoesNotExist:
		self.stderr.write(f'genetic id {genetic_id} missing')
		return None
	except DataFileAssignment.DoesNotExist:
		self.stderr.write(f'genetic id {id1} does not have file {filepath}')
		return None
		
version_re_compiled = re.compile(r'\d+$')
def version_from_str(s):
	match = re.search(version_re_compiled, s)
	if match:
		return int(match.group(0))
	else:
		return None

class Command(BaseCommand):
	help = "This command loads data Inigo's analysis for family relations"
	
	def add_arguments(self, parser):
		parser.add_argument('family_relation_file')
		parser.add_argument('-r', '--rollback', action='store_true')
		
	def handle(self, *args, **options):
		family_relation_file = options['family_relation_file']
		failure = False
		with transaction.atomic():
			with open(family_relation_file) as f:
				f.readline() # discard header
				for line in f:
					# ID1	ID2	Degree	Type	PointerID1	PointerID2	Method	Score	Comments	Kinship
					fields = re.split('\t|\n', line)
					fields = [x if x != '..' else '' for x in fields]
					id1 = fields[0]
					id2 = fields[1]
					degree = degree_to_float(fields[2])
					degree_type = fields[3]
					file1 = fields[4]
					file2 = fields[5]
					method = fields[6]
					score = fields[7]
					comments = fields[8]
					version = fields[9]
					
					if score != '':
						raise NotImplementedError('non-empty score')
					
					# check that genetic IDs have data files associated with them
					if person1 = genetic_id_has_file(id1, file1) and person2 = genetic_id_has_file(id2, file2):
						method, method_created = FamilyRelationshipMethod.objects.get_or_create(method=method)
						relationship, created = FamilyRelationship.objects.get_or_create(person1=person1, person2=person2, method=method)
						relationship.degree = degree
						relationship.relationship, relationship_type_created = FamilyRelationshipType.objects.get_or_create(relationship=degree_type)
						relationship.version = version_from_str(version)
						relationship.notes = comments
						relationship.save()
						if not created:
							self.stderr.write(f'relationship between {id1} and {id2} already exists')
							failure = True
					else: # genetic analysis missing
						failure = True
					
			if failure or options['rollback']:
				transaction.set_rollback(True)
