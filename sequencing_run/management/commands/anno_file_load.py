from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db import transaction
from django.db.models import Count, Q

from pathlib import Path
import re

from samples.models import Sample, SpecialRestriction, DataFileType, DataFile, DataInstance, DataFileAssignment, PublicationLabels, Publication, SID_IID_REGEX
from sequencing_run.models import GeneticAnalysis

class Command(BaseCommand):
	help = 'This command loads data from the Reich Lab annotation file v.64.2'
	
	def add_arguments(self, parser):
		parser.add_argument('annotation_file')
		parser.add_argument('-r', '--rollback', action='store_true')
		
	def handle(self, *args, **options):
		annotation_filename = options['annotation_file']
		failure = False
		with transaction.atomic():
			with open(annotation_filename) as f:
				f.readline() # discard header
				for line in f:
					try:
						raw_fields = [x.strip() for x in re.split('\t|\n', line)]
						fields = [x if x != '..' else '' for x in raw_fields] # remove this anno file representation for null
						genetic_id = fields[1]
						individual_id = fields[2] # check this against data entries
						publication_abbreviation = fields[7]
						permanent_repository = fields[9]
						special_restriction = fields[21]
						
						libraries = fields[56]
						assessment = fields[58]
						
						mt_bam = fields[27]
						
						pulldown_log = fields[29]
						pulldown_id = fields[30]
						autosome_bam = fields[31]
						read_groups_or_hetfa_or_ranfa = fields[32]
					except IndexError as e:
						self.stderr.write(line)
						self.stdout.write(line)
						raise e
					
					# create data files
					assigned_data = [] # for assignment to data instance
					# MT bam
					mt_bam_type, created = DataFileType.objects.get_or_create(name='MT bam')
					if len(mt_bam) > 0:
						mt_data, created = DataFile.objects.get_or_create(file_type=mt_bam_type, path=mt_bam)
						assigned_data.append(mt_data)
					else:
						mt_data = None
					# autosomal bam
					autosomal_bam_type, created = DataFileType.objects.get_or_create(name='autosomal bam')
					if len(autosome_bam) > 0:
						autosomal_data, created = DataFile.objects.get_or_create(file_type=autosomal_bam_type, path=autosome_bam)
						assigned_data.append(autosomal_data)
					else:
						autosomal_data = None
					# hetfa or ranfa or read groups TODO
					read_groups = []
					hetfa_data = None
					ranfa_data = None
					fixme_data = None
					if 'hetfa' in read_groups_or_hetfa_or_ranfa:
						hetfa_type, created = DataFileType.objects.get_or_create(name='hetfa')
						hetfa_data, created = DataFile.objects.get_or_create(file_type=hetfa_type, path=read_groups_or_hetfa_or_ranfa)
						assigned_data.append(hetfa_data)
					elif 'ranfa' in read_groups_or_hetfa_or_ranfa:
						ranfa_type, created = DataFileType.objects.get_or_create(name='ranfa')
						ranfa_data, created = DataFile.objects.get_or_create(file_type=ranfa_type, path=read_groups_or_hetfa_or_ranfa)
						assigned_data.append(ranfa_data)
					elif 'VCF' in read_groups_or_hetfa_or_ranfa or read_groups_or_hetfa_or_ranfa.endswith('.fa'):
						fixme_type, created = DataFileType.objects.get_or_create(name='fixme')
						fixme_data, created = DataFile.objects.get_or_create(file_type=fixme_type, path=read_groups_or_hetfa_or_ranfa)
						assigned_data.append(fixme_data)
					elif len(read_groups_or_hetfa_or_ranfa) > 0:
						read_groups = read_groups_or_hetfa_or_ranfa.split(':')
					
					match = re.fullmatch(SID_IID_REGEX, individual_id)
					sample = None
					if match:
						try:
							sample_id_number = int(match.groupdict()['sample'])
							sample = Sample.objects.get(reich_lab_id=sample_id_number, control='')
						except Sample.DoesNotExist as e:
							print(f'{sample_id_number} does not exist')
							print(line)
							#raise e
						except Sample.MultipleObjectsReturned as e:
							self.stderr.write(f'{sample_id_number} has {str(e)}')
							raise e
					else:
						try:
							sample = Sample.objects.get(external_id=individual_id)
						except Sample.DoesNotExist:
							pass
					if sample is None:
						self.stderr.write(f'{individual_id} not found')
						failure = True
					else:
						if len(special_restriction) > 0 and special_restriction != '0':
							sample.special_restrictions = True
							sample.special_restriction, created = SpecialRestriction.objects.get_or_create(anno_file_key=special_restriction, description=str(special_restriction))
							sample.save()

					try:
						num_data = 0
						num_read_groups = len(read_groups)
						if mt_data:
							num_data += max(num_read_groups, 1)
						if autosomal_data:
							num_data += max(num_read_groups, 1)
						if hetfa_data:
							num_data += 1
						if ranfa_data:
							num_data += 1
						if fixme_data:
							num_data += 1
						if num_data == 0 and 'HO' not in genetic_id:
							self.stderr.write(line)
							self.stderr.write(f'{genetic_id} has no files')
						data_instance = DataInstance.objects.annotate(total_files=Count('data_files'), matching_files=Count('data_files', filter=Q(data_files__in=assigned_data)) ).get(primary_sample=sample, libraries=libraries)
					# except DataInstance.MultipleObjectsReturned:
					# 	instances = DataInstance.objects.filter(primary_sample=sample, libraries=libraries, data_files__in=[mt_data, autosomal_data]).distinct()
					# 	for instance in instances:
					# 		print(str(instance))
					# 		print(line)
					except DataInstance.DoesNotExist:
						#print(genetic_id)
						data_instance = DataInstance(primary_sample=sample, libraries=libraries)
						data_instance.save()
						# add bams with read groups
						if len(read_groups) == 0: # blank indicates to use all read groups
							read_groups=['']
						for read_group in read_groups:
							if mt_data:
								DataFileAssignment.objects.create(data_file=mt_data, collection=data_instance, read_group=read_group)
							if autosomal_data:
								DataFileAssignment.objects.create(data_file=autosomal_data, collection=data_instance, read_group=read_group)
						if hetfa_data:
							DataFileAssignment.objects.create(data_file=hetfa_data, collection=data_instance, read_group='')
						if ranfa_data:
							DataFileAssignment.objects.create(data_file=ranfa_data, collection=data_instance, read_group='')
						if fixme_data:
							DataFileAssignment.objects.create(data_file=fixme_data, collection=data_instance, read_group='')
					
					# genetic id
					genetic_analysis, created = GeneticAnalysis.objects.get_or_create(data_instance=data_instance, genetic_id=genetic_id, pulldown_id=pulldown_id)
					genetic_analysis.permanent_repository = permanent_repository
					genetic_analysis.save()
					
					if publication_abbreviation != 'Unpublished' and len(publication_abbreviation) > 0:
						try:
							search = publication_abbreviation.split()[0] # notes may follow, ignore these
							publication = Publication.objects.get(abbreviation=search)
						
							label, created = PublicationLabels.objects.get_or_create(sample=sample, publication=publication, genetic_id=genetic_id, genetic_id_entry=genetic_analysis)
						except Publication.DoesNotExist as e:
							if 'Unpublished' in publication_abbreviation:
								self.stderr.write(f'Ignored publication {publication_abbreviation}')
							else:
								self.stderr.write(f'Publication {publication_abbreviation} not found')
								# raise e
						except IndexError as e:
							self.stderr.write(line)
							raise e
					
			if failure or options['rollback']:
				raise ValueError('rollback exception')
