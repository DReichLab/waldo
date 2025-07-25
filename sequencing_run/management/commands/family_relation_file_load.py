from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db import transaction
from django.db.models import Count, Q

from pathlib import Path
import re

from samples.models import Sample, SpecialRestriction, DataFileType, DataFile, DataInstance, DataFileAssignment, PublicationLabels, Publication, SID_IID_REGEX, AssessmentCategory, get_sample_by_anyid
from sequencing_run.models import GeneticAnalysis, FamilyRelationshipMethod, FamilyRelationship, FamilyRelationshipType

def degree_to_float(s):
	degree_str = s.split('-')[0]
	if degree_str == 'Dup':
		degree = 0.0
	else:
		degree = float(degree_str)
	if '-' in s:
		degree += 0.5
	return degree
		
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
		parser.add_argument('-d', '--disable_rollback', action='store_true')
		
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
						
					if file1 == '':
						self.stderr.write(f'{id1} is missing file')
					if file2 == '':
						self.stderr.write(f'{id2} is missing file')
					
					# check that genetic IDs have data files associated with them
					person1, person1_file = self.setup_data(id1, file1)
					person2, person2_file = self.setup_data(id2, file2)
					if person1 and person2:
						method, method_created = FamilyRelationshipMethod.objects.get_or_create(method=method)
						try:
							relationship = FamilyRelationship.objects.get(person1=person1, person1_file=person1_file, person2=person2, person2_file=person2_file, method=method)
							self.stderr.write(f'relationship between {id1} and {id2} already exists')
							failure = True
						except FamilyRelationship.DoesNotExist:
							relationship = FamilyRelationship(person1=person1, person1_file=person1_file, person2=person2, person2_file=person2_file, method=method)
						relationship.degree = degree
						relationship.relationship, relationship_type_created = FamilyRelationshipType.objects.get_or_create(relationship=degree_type)
						relationship.version = version_from_str(version)
						relationship.notes = comments
						relationship.save()
					else:
						failure = True
					
			if not options['disable_rollback'] and (failure or options['rollback']):
				transaction.set_rollback(True)
				
	def setup_data(self, individual, filepath):
		autosomal_data_type, ignored = DataFileType.objects.get_or_create(name='autosomal bam')
		data_file, created = DataFile.objects.get_or_create(file_type=autosomal_data_type, path=filepath)
		
		try:
			data_instance = DataInstance.objects.get(data_files__in=[data_file.id])
		except DataInstance.DoesNotExist:
			try:
				sample = get_sample_by_anyid(individual)
			except Sample.DoesNotExist as e:
				self.stderr.write(individual)
				raise e
			data_instance = DataInstance.objects.create(primary_sample=sample)
			data_instance.data_files.add(data_file)
		return data_instance, data_file
