from django.db import transaction
from django.db.models import Q
import re
import sys
from samples.models import get_value, Sample, ArchaeologicalAssemblage, Location, parse_sample_string, Publication, PublicationType, PublicationLabels, ExtractionBatchLayout, Lysate, Period, Culture, SkeletalElementCategory, AssessmentCategory, get_sample_by_anyid, DataInstance, data_instance_get, data_instance_create
from sequencing_run.models import GeneticAnalysis
from samples.spreadsheet import spreadsheet_pass

def reich_sample_number(s):
	if s.startswith('I'):
		return int(s[1:])
	try:
		sample_number, control = parse_sample_string(s)
		return sample_number
	except ValueError:
		return int(s)
		
# default behavior of Python bool
def boolean_from_str(s):
	s_lower = s.lower()
	if s_lower == 'f' or s_lower == 'false':
		return False
	return bool(s)

sample_headers = ['sample_id', 'external_id', 'site_name', 'burial_code', 'burial_subcode', 'excavation_year', 'excavation_grid', 'skeletal_code', 'skeletal_element', 'skeletal_element_category', 'sample_date', 'average_bp_date', 'date_stdev', 'date_fix_flag', 'morphological_sex', 'morphological_age', 'morphological_age_range', 'periods', 'cultures', 'group_label_use_country', 'group_label_use_level_1', 'group_label_use_level_2', 'group_label_use_site', 'group_label_use_period', 'group_label_use_culture']
def sample_site_update(sample_file, user):
	messages = []
	with transaction.atomic():
		for sample_row in spreadsheet_pass(sample_file):
			row = sample_row.spreadsheet_row_to_obj()
			# Reich lab IDs will already exist
			if row.sample_id is not None and len(row.sample_id) > 0:
				sample = Sample.objects.get(reich_lab_id=reich_sample_number(row.sample_id))
				if len(row.external_id) > 0:
					sample.external_id = row.external_id
				else:
					sample.external_id = None
				sample_created = False
			else: # external IDs can be added
				sample, sample_created = Sample.objects.get_or_create(external_id=row.external_id)
				if sample_created:
					messages.append(f'created sample external id: {row.external_id}')
				sample.master_id = row.external_id
			
			if len(row.site_name) == 0:
				raise ValueError(f'Sample {row.sample_id} {row.external_id} needs a site name')
			site = Location.objects.get(site=row.site_name)
			
			#if len(row.burial_code) == 0:
				#raise ValueError(f'Sample {row.sample_id} {row.external_id} needs a burial_code')
			create_archaeological_assemblage = False
			if sample.archaeological_assemblage:
				arch_assemblage = sample.archaeological_assemblage
				if Sample.objects.filter(archaeological_assemblage=arch_assemblage).count() > 1:
					if arch_assemblage.burial_code != row.burial_code or arch_assemblage.site != site:
						# create a new archaeological_assemblage to preserve site and burial code for other samples
						create_archaeological_assemblage = True
				else: # change site and burial code, only for this sample
					arch_assemblage.site = site
					arch_assemblage.burial_code = row.burial_code
					arch_assemblage.save(save_user=user)
			else:
				try:
					arch_assemblage = ArchaeologicalAssemblage.objects.get(site=site, burial_code=row.burial_code)
				except ArchaeologicalAssemblage.DoesNotExist:
					create_archaeological_assemblage = True
			if create_archaeological_assemblage:
				arch_assemblage = ArchaeologicalAssemblage()
				arch_assemblage.burial_code = row.burial_code
				arch_assemblage.site = site
				messages.append(f'created archeological assemblage {site.site}: {arch_assemblage.burial_code}')
				arch_assemblage.save(save_user=user)
			sample.archaeological_assemblage = arch_assemblage
			
			sample.burial_subcode = row.burial_subcode
			if sample_created:
				sample.collaborator_code = row.skeletal_code
			sample.skeletal_code = row.skeletal_code
			sample.skeletal_element = row.skeletal_element
			if len(row.skeletal_element_category) > 0:
				sample.skeletal_element_category = SkeletalElementCategory.objects.get(category__iexact=row.skeletal_element_category)
			sample.sample_date = row.sample_date
			sample.average_bp_date = float(row.average_bp_date) if len(row.average_bp_date) > 0 else None
			sample.date_stdev = float(row.date_stdev) if len(row.date_stdev) > 0 else None
			sample.date_fix_flag = row.date_fix_flag
			sample.morphological_sex = row.morphological_sex
			sample.morphological_age = row.morphological_age
			sample.morphological_age_range = row.morphological_age_range
			
			# abbreviations
			# clear periods and cultures and replace with those listed
			sample.periods.clear()
			for period in row.periods.split():
				sample.periods.add(Period.objects.get(abbreviation=period))
			sample.cultures.clear()
			for culture in row.cultures.split():
				sample.cultures.add(Culture.objects.get(abbreviation=culture))
			
			sample.group_label_use_country = boolean_from_str(row.group_label_use_country)
			sample.group_label_use_level_1 = boolean_from_str(row.group_label_use_level_1)
			sample.group_label_use_level_2 = boolean_from_str(row.group_label_use_level_2)
			sample.group_label_use_site = boolean_from_str(row.group_label_use_site)
			sample.group_label_use_period = boolean_from_str(row.group_label_use_period)
			sample.group_label_use_culture = boolean_from_str(row.group_label_use_culture)
			sample.save(save_user=user)
				
	return '\n'.join(messages)
	
# inverse of sample_site_update
# provide the current values of sample fields for an update
def sample_site_values(sample):
	values = {}
	if sample.reich_lab_id:
		values['sample_id'] = str(sample)
		values['external_id'] = sample.external_id
	else: # external
		values['sample_id'] = ''
		values['external_id'] = str(sample)
	values['site_name'] = get_value(sample, 'archaeological_assemblage', 'site', 'site')
	values['burial_code'] = get_value(sample, 'archaeological_assemblage', 'burial_code')
	values['skeletal_element_category'] = get_value(sample, 'skeletal_element_category', 'category')
	
	for key in ['burial_subcode', 
	'excavation_year',
	'excavation_grid',
	'skeletal_code',
	'skeletal_element',
	'sample_date', 
	'average_bp_date', 
	'date_stdev',
	'date_fix_flag',
	'morphological_sex',
	'morphological_age',
	'morphological_age_range',
	'group_label_use_country',
	'group_label_use_level_1',
	'group_label_use_level_2',
	'group_label_use_site',
	'group_label_use_period',
	'group_label_use_culture']:
		values[key] = getattr(sample, key)
	
	values['periods'] = ' '.join([p.abbreviation for p in sample.periods.all().order_by('date_start', 'abbreviation')])
	values['cultures'] = ' '.join([p.abbreviation for p in sample.cultures.all().order_by('date_start', 'abbreviation')])
	
	ordered_values = [values[key] for key in sample_headers]
	return ordered_values

publication_headers = ['abbreviation', 'title', 'first_author', 'year', 'journal', 'pages', 'author_list', 'url', 'publication_type', 'notes']
def publication_batch_update(batch_file, user):
	messages = []
	with transaction.atomic():
		for row in spreadsheet_pass(batch_file):
			pub_row = row.spreadsheet_row_to_obj()
			publication, created = Publication.objects.get_or_create(abbreviation=pub_row.abbreviation)
			for field in publication_headers[1:-1]:
				if field not in ['year']:
					setattr(publication, field, getattr(pub_row, field))
			if len(pub_row.year) > 0:
				publication.year = int(pub_row.year)
			if len(pub_row.publication_type) > 0:
				publication.publication_type = PublicationType.objects.get(category=pub_row.publication_type)
			publication.save(save_user=user)
			messages += [f'{publication.abbreviation} {" created" if created else " updated. "}']
	return '\n'.join(messages)

publication_sample_assign_headers = ['sample_id', 'external_id', 'publication_abbreviation', 'paper_individual_id', 'paper_group_label', 'digital_accession_number', 'genetic_id']
def publication_sample_assign(batch_file, user):
	messages = []
	with transaction.atomic():
		for row in spreadsheet_pass(batch_file):
			row_obj = row.spreadsheet_row_to_obj()
			if len(row_obj.sample_id) > 0:
				sample = Sample.objects.get(reich_lab_id=reich_sample_number(row_obj.sample_id))
				sample_label = sample.reich_lab_id
			else:
				sample = Sample.objects.get(external_id=row_obj.external_id)
				sample_label = sample.external_id
			publication = Publication.objects.get(abbreviation=row_obj.publication_abbreviation)
			try:
				pairing = PublicationLabels.objects.get(sample=sample, publication=publication)
			except PublicationLabels.DoesNotExist:
				pairing = PublicationLabels()
				pairing.sample = sample
				pairing.publication = publication
			if len(row_obj.paper_individual_id) > 0:
				pairing.individual_id = row_obj.paper_individual_id
			if len(row_obj.paper_group_label) > 0:
				pairing.group_label = row_obj.paper_group_label
			if len(row_obj.digital_accession_number) > 0:
				pairing.digital_accession_number = row_obj.digital_accession_number
			if len(row_obj.genetic_id) > 0:
				pairing.genetic_id = row_obj.genetic_id
				pairing.genetic_id_entry = GeneticAnalysis.objects.get(genetic_id=row_obj.genetic_id)
				pairing.published_data = pairing.genetic_id_entry.data_instance
			pairing.save(save_user=user)
			messages += [f'{sample_label} was published in {publication.title}']
	return '\n'.join(messages)
	
PROVISIONAL = 'Provisional'
genetic_analysis_headers = ['genetic_id', 'primary_sample', 'nuclear_bam', 'nuclear_read_groups', 'mt_bam', 'mt_read_groups', 'libraries', 'pulldown_id', 'first_release']
def genetic_analysis_setup(batch_file, user, allow_updates=False):
	messages = []
	with transaction.atomic():
		try:
			provisional_assessment = AssessmentCategory.objects.get(category__iexact=PROVISIONAL)
		except AssessmentCategory.DoesNotExist:
			provisional_assessment = AssessmentCategory.objects.create(category=PROVISIONAL, sort_order=15)
		for row in spreadsheet_pass(batch_file):
			row_obj = row.spreadsheet_row_to_obj()
			genetic_id = row_obj.genetic_id
			sample = get_sample_by_anyid(row_obj.primary_sample)
			nuclear_read_groups = row_obj.nuclear_read_groups.split()
			mt_read_groups = row_obj.mt_read_groups.split()
			
			try:
				data_instance = data_instance_get(sample, row_obj.nuclear_bam, nuclear_read_groups, row_obj.mt_bam, mt_read_groups, row_obj.libraries, exact=True)
				data_instance_created = False
			except DataInstance.DoesNotExist:
				data_instance = data_instance_create(sample, row_obj.nuclear_bam, nuclear_read_groups, row_obj.mt_bam, mt_read_groups, row_obj.libraries, user)
				data_instance_created = True
			
			try:
				genetic_analysis = GeneticAnalysis.objects.get(genetic_id=genetic_id)
				if not allow_updates:
					raise ValueError(f'{genetic_id} already exists.')
				genetic_analysis_created = False
			except GeneticAnalysis.DoesNotExist:
				genetic_analysis = GeneticAnalysis()
				genetic_analysis.genetic_id = genetic_id
				genetic_analysis.primary_sample = data_instance.primary_sample
				genetic_analysis.assessment = provisional_assessment
				genetic_analysis_created = True
			genetic_analysis.data_instance = data_instance
			genetic_analysis.pulldown_id = row_obj.pulldown_id
			genetic_analysis.first_release = row_obj.first_release
			genetic_analysis.save(save_user=user)
			messages += [f'Genetic analysis {genetic_id} {"created" if genetic_analysis_created else "updated"}. Data instance {data_instance.id} {"created" if data_instance_created else "updated"}.']
	return '\n'.join(messages)

lost_lysate_headers = ['lysate_id', 'notes']
def lost_lysate_batch_update(batch_file, user):
	messages = []
	with transaction.atomic():
		for row in spreadsheet_pass(batch_file):
			row_obj = row.spreadsheet_row_to_obj()
			lysate = Lysate.objects.get(lysate_id=row_obj.lysate_id)
			lysate_remaining = lysate.remaining()
			lost_lysate, created = ExtractionBatchLayout.objects.get_or_create(lysate=lysate, extract_batch=None)
			lost_lysate.notes = row_obj.notes
			if created:
				lost_lysate.lysate_volume_used = lysate_remaining
			else:
				lost_lysate.lysate_volume_used += lysate_remaining
			lost_lysate.save(save_user=user)
			messages += [f'{lost_lysate.lysate.lysate_id} remaining lysate lost {lost_lysate.lysate_volume_used}. ']
	return '\n'.join(messages)
