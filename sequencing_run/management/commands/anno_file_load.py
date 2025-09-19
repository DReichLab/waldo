from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db import transaction
from django.db.models import Count, Q

from pathlib import Path
import re

from samples.models import Sample, SpecialRestriction, DataFileType, DataFile, DataInstance, DataFileAssignment, PublicationLabels, Publication, SID_IID_REGEX, AssessmentCategory
from sequencing_run.models import GeneticAnalysis

def data_instance_match(data_instance, sample, data_files, libraries, read_groups, types_with_read_groups):
	if data_instance.primary_sample != sample or data_instance.libraries != libraries:
		return False
	assigned = DataFileAssignment.objects.filter(collection=data_instance)
	if len(data_files) != len(assigned):
		return False
	for data_file in data_files:
		try:
			if data_file.file_type in types_with_read_groups and len(read_groups) > 0:
				for read_group in read_groups:
					assigned.get(collection=data_instance, data_file=data_file, read_group=read_group)
			else:
				assigned.get(collection=data_instance, data_file=data_file, read_group='')
		except DataFileAssignment.DoesNotExist:
			return False
	return True

class Command(BaseCommand):
	help = 'This command loads data from the Reich Lab annotation file v.64.2. Skips header line'
	
	def add_arguments(self, parser):
		parser.add_argument('annotation_file')
		parser.add_argument('-r', '--rollback', action='store_true')
		parser.add_argument('-d', '--disable_rollback', action='store_true')
		parser.add_argument('-n', '--genetic_id_column', type=int, help='0-indexed column containing genetic ID')
		
	def find_data_instance(self, sample, data_files, libraries, read_groups, types_with_read_groups):
		candidates = DataInstance.objects.filter(primary_sample=sample, libraries=libraries)
		passed = []
		for candidate in candidates:
			if data_instance_match(candidate, sample, data_files, libraries, read_groups, types_with_read_groups):
				passed.append(candidate)
		if len(passed) > 1:
			for data_instance in passed:
				self.stderr.write(str(data_instance))
			raise ValueError('Multiple data instances')
		if len(passed) == 1:
			return passed[0]
		return None
		
	def handle(self, *args, **options):
		annotation_filename = options['annotation_file']
		failure = False
		with transaction.atomic():
			mt_bam_type, created = DataFileType.objects.get_or_create(name='MT bam')
			autosomal_bam_type, created = DataFileType.objects.get_or_create(name='autosomal bam')
			mt_fasta_type, created = DataFileType.objects.get_or_create(name='MT fasta')
			hetfa_type, created = DataFileType.objects.get_or_create(name='hetfa')
			ranfa_type, created = DataFileType.objects.get_or_create(name='ranfa')
			
			types_with_read_groups = [mt_bam_type, autosomal_bam_type]
			with open(annotation_filename) as f:
				f.readline() # discard header
				for line in f:
					try:
						raw_fields = [x.strip() for x in re.split('\t|\n', line)]
						fields = [x if x != '..' else '' for x in raw_fields] # remove this anno file representation for null
						genetic_id = fields[1] if not options['genetic_id_column'] else fields[options['genetic_id_column']]
						individual_id = fields[2] # check this against data entries
						publication_abbreviation = fields[7]
						permanent_repository = fields[9]
						special_restriction = fields[21]
						
						libraries = fields[56]
						assessment = fields[58]
						
						mt_bam = fields[26]
						mt_fasta = fields[27]
						
						pulldown_log = fields[29]
						pulldown_id = fields[30]
						autosome_bam = fields[31]
						read_groups_or_hetfa_or_ranfa = fields[32]
					except IndexError as e:
						self.stderr.write(line)
						raise e
					
					# create data files
					assigned_data = [] # for assignment to data instance
					# MT bam
					if len(mt_bam) > 0:
						mt_bam_suffix = Path(mt_bam).suffix
						if mt_bam_suffix not in ['.bam', '.cram']:
							self.stderr.write(f'Unexpected mt_bam suffix {mt_bam_suffix} {mt_bam}')
						mt_data, created = DataFile.objects.get_or_create(file_type=mt_bam_type, path=mt_bam)
						assigned_data.append(mt_data)
					else:
						mt_data = None
					# MT fasta
					if len(mt_fasta) > 0:
						mt_fasta_data, DataFile.objects.get_or_create(file_type=mt_fasta_type, path=mt_fasta)
						assigned_data.append(mt_fasta_data)
					else:
						mt_fasta_data = None
					# autosomal bam
					if len(autosome_bam) > 0:
						autosome_bam_suffix = Path(autosome_bam).suffix
						if autosome_bam_suffix not in ['.bam', '.cram']:
							self.stderr.write(f'Unexpected autosome_bam suffix {autosome_bam_suffix} {autosome_bam}')
						autosomal_data, created = DataFile.objects.get_or_create(file_type=autosomal_bam_type, path=autosome_bam)
						assigned_data.append(autosomal_data)
					else:
						autosomal_data = None
					# hetfa or ranfa or read groups
					read_groups = []
					repeated_read_groups = False
					hetfa_data = None
					ranfa_data = None
					fixme_data = None
					if 'hetfa' in read_groups_or_hetfa_or_ranfa:
						hetfa_data, created = DataFile.objects.get_or_create(file_type=hetfa_type, path=read_groups_or_hetfa_or_ranfa)
						assigned_data.append(hetfa_data)
					elif 'ranfa' in read_groups_or_hetfa_or_ranfa:
						ranfa_data, created = DataFile.objects.get_or_create(file_type=ranfa_type, path=read_groups_or_hetfa_or_ranfa)
						assigned_data.append(ranfa_data)
					elif 'VCF' in read_groups_or_hetfa_or_ranfa or read_groups_or_hetfa_or_ranfa.endswith('.fa'):
						fixme_type, created = DataFileType.objects.get_or_create(name='fixme')
						fixme_data, created = DataFile.objects.get_or_create(file_type=fixme_type, path=read_groups_or_hetfa_or_ranfa)
						assigned_data.append(fixme_data)
					elif len(read_groups_or_hetfa_or_ranfa) > 0:
						read_groups_list = read_groups_or_hetfa_or_ranfa.split(':')
						# remove duplicates from this list
						for read_group in read_groups_list:
							if read_group not in read_groups:
								read_groups.append(read_group)
							else:
								repeated_read_groups = True
								self.stderr.write(f'{genetic_id} read group repeated {read_group}')
					if repeated_read_groups:
						read_groups = []
					
					match = re.fullmatch(SID_IID_REGEX, individual_id)
					sample = None
					if match:
						try:
							sample_id_number = int(match.groupdict()['sample'])
							sample = Sample.objects.get(reich_lab_id=sample_id_number, control='')
						except Sample.DoesNotExist as e:
							print(f'{sample_id_number} does not exist')
							# print(line)
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
						continue
					else:
						if len(special_restriction) > 0 and special_restriction != '0':
							sample.special_restrictions = True
							sample.special_restriction, created = SpecialRestriction.objects.get_or_create(anno_file_key=special_restriction, description=str(special_restriction))
							sample.save()

					num_data = 0
					num_read_groups = len(read_groups)
					if mt_data:
						num_data += max(num_read_groups, 1)
					if autosomal_data:
						num_data += max(num_read_groups, 1)
					if mt_fasta_data:
						num_data += 1
					if hetfa_data:
						num_data += 1
					if ranfa_data:
						num_data += 1
					if fixme_data:
						num_data += 1
					if num_data == 0 and 'HO' not in genetic_id:
						# self.stderr.write(line)
						self.stderr.write(f'{genetic_id} has no files')
					data_instance = self.find_data_instance(sample, assigned_data, libraries, read_groups, types_with_read_groups)
					if data_instance is None:
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
					try:
						genetic_analysis = GeneticAnalysis.objects.get(genetic_id=genetic_id, pulldown_id=pulldown_id)
						genetic_analysis.data_instance = data_instance
					except GeneticAnalysis.DoesNotExist:
						genetic_analysis, created = GeneticAnalysis.objects.get_or_create(data_instance=data_instance, genetic_id=genetic_id, pulldown_id=pulldown_id)
					genetic_analysis.permanent_repository = permanent_repository
					try:
						genetic_analysis.assessment = AssessmentCategory.objects.get(category__iexact=assessment)
					except AssessmentCategory.DoesNotExist:
						genetic_analysis.assessment = AssessmentCategory.objects.create(category=assessment, sort_order=10000)
					genetic_analysis.save()
					
					if publication_abbreviation != 'Unpublished' and len(publication_abbreviation) > 0:
						try:
							search = publication_abbreviation.split()[0] # notes may follow, ignore these
							publication, created = Publication.objects.get_or_create(abbreviation=search)
						
							label, created = PublicationLabels.objects.get_or_create(sample=sample, publication=publication, genetic_id=genetic_id, genetic_id_entry=genetic_analysis)
						except Publication.DoesNotExist as e:
							if 'Unpublished' in publication_abbreviation:
								self.stderr.write(f'Ignored publication {publication_abbreviation}')
							else:
								self.stderr.write(f'Publication {publication_abbreviation} not found')
								# raise e
						except Exception as e:
							self.stderr.write(line)
							raise e
					
			if not options['disable_rollback'] and (failure or options['rollback']):
				self.stderr.write('rolling back')
				transaction.set_rollback(True)
