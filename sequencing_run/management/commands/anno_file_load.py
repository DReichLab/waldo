from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db import transaction
from django.db.models import Count, Q

from pathlib import Path
import re

from samples.models import Sample, DataFileType, DataFile, DataInstance, PublicationLabels, Publication, SID_IID_REGEX
from sequencing_run.models import GeneticAnalysis

class Command(BaseCommand):
	help = 'This command loads data from the Reich Lab annotation file v.64.2'
	
	def add_arguments(self, parser):
		parser.add_argument('annotation_file')
		
	def handle(self, *args, **options):
		annotation_filename = options['annotation_file']
		with transaction.atomic():
			with open(annotation_filename) as f:
				f.readline() # discard header
				for line in f:
					fields = [x.strip() for x in re.split('\t|\n', line)]
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
					
					# create data files
					mt_bam_type, created = DataFileType.objects.get_or_create(name='MT bam')
					mt_data, created = DataFile.objects.get_or_create(file_type=mt_bam_type, path=mt_bam)
					autosomal_bam_type, created = DataFileType.objects.get_or_create(name='autosomal bam')
					autosomal_data, created = DataFile.objects.get_or_create(file_type=autosomal_bam_type, path=autosome_bam)
					
					match = re.fullmatch(SID_IID_REGEX, individual_id)
					if match:
						try:
							sample_id_number = int(match.groupdict()['sample'])
							sample = Sample.objects.get(reich_lab_id=sample_id_number)
						except Sample.DoesNotExist as e:
							print(sample_id_number)
							print(line)
							#raise e
						except Sample.MultipleObjectsReturned as e:
							self.stderr.write(f'{sample_id_number} has {str(e)}')

					else:
						try:
								sample = Sample.objects.get(external_id=individual_id)
						except Sample.DoesNotExist:
								self.stderr.write(f'{individual_id} not found')
					if sample is None:
						self.stderr.write(f'{individual_id} not found')

					try:
						assigned_data = [mt_data, autosomal_data]
						num_data = len(assigned_data)
						data_instance = DataInstance.objects.annotate(total_files=Count('data_files'), matching_files=Count('data_files', filter=Q(data_files__in=assigned_data)) ).get(primary_sample=sample, libraries=libraries)
					except DataInstance.MultipleObjectsReturned:
						instances = DataInstance.objects.filter(primary_sample=sample, libraries=libraries, data_files__in=[mt_data, autosomal_data]).distinct()
						for instance in instances:
							print(str(instance))
							print(line)
					except DataInstance.DoesNotExist:
						data_instance = DataInstance(primary_sample=sample, libraries=libraries)
						data_instance.save()
						data_instance.data_files.add(mt_data)
						data_instance.data_files.add(autosomal_data)
					
					# genetic id
					genetic_analysis, created = GeneticAnalysis.objects.get_or_create(data_instance=data_instance, genetic_id=genetic_id, pulldown_id=pulldown_id)
					genetic_analysis.permanent_repository = permanent_repository
					genetic_analysis.save()
					
					publication, created = Publication.objects.get_or_create(abbreviation=publication_abbreviation)
					label, created = PublicationLabels.objects.get_or_create(sample=sample, publication=publication, genetic_id=genetic_id, genetic_id_entry=genetic_analysis)
					
