from django.db import transaction
from django.db.models import Q
import re
import sys
from samples.models import Sample, ArchaeologicalAssemblage, Location, parse_sample_string, Publication, PublicationType, PublicationLabels
from samples.spreadsheet import spreadsheet_pass

def reich_sample_number(s):
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

sample_headers = ['sample_id', 'skeletal_code', 'site_name', 'burial_code', 'periods', 'cultures', 'group_label_use_country', 'group_label_use_site', 'group_label_use_period', 'group_label_use_culture']
def sample_site_update(sample_file, user):
	messages = []
	with transaction.atomic():
		for sample_row in spreadsheet_pass(sample_file):
			row = sample_row.spreadsheet_row_to_obj()
			sample = Sample.objects.get(reich_lab_id=reich_sample_number(row.sample_id))
			
			try:
				site = Location.objects.get(site=row.site_name)
			except Location.DoesNotExist:
				site = Location()
				site.site = row.site_name
				site.save(save_user=user)
				messages.append(f'created location {row.site_name}')
			
			if sample.archaeological_assemblage:
				if sample.archaeological_assemblage.burial_code != row.burial_code:
					raise ValueError(f'{row.sample_id} already has burial code {sample.archaeological_assemblage.burial_code}. Did not replace with {row.burial_code}')
			else:
				try:
					arch_assemblage = ArchaeologicalAssemblage.objects.get(site=site, burial_code=row.burial_code)
				except ArchaeologicalAssemblage.DoesNotExist:
					arch_assemblage = ArchaeologicalAssemblage()
					arch_assemblage.burial_code = row.burial_code
					arch_assemblage.site = site
					messages.append(f'created archeological assemblage {site.site}: {arch_assemblage.burial_code}')
					arch_assemblage.save(save_user=user)
				sample.archaeological_assemblage = arch_assemblage
			sample.skeletal_code_renamed = row.skeletal_code
			
			'''
			# TODO revisit to allow multiple
			sample.publications.add(find_publication(row.publications.split()))
			# abbreviations
			for period in row.periods.split():
				sample.periods.add(Period.objects.get(abbreviation=period))
			for culture in row.cultures.split():
				sample.cultures.add(Culture.objects.get(abbreviation=culture))
			'''
			
			sample.group_label_use_country = boolean_from_str(row.group_label_use_country)
			sample.group_label_use_site = boolean_from_str(row.group_label_use_site)
			sample.group_label_use_period = boolean_from_str(row.group_label_use_period)
			sample.group_label_use_culture = boolean_from_str(row.group_label_use_culture)
			sample.save(save_user=user)
				
	return '\n'.join(messages)

publication_headers = ['title', 'first_author', 'year', 'journal', 'pages', 'author_list', 'url', 'publication_type']
def publication_batch_update(batch_file, user):
	messages = []
	with transaction.atomic():
		for row in spreadsheet_pass(batch_file):
			pub_row = row.spreadsheet_row_to_obj()
			publication, created = Publication.objects.get_or_create(title=pub_row.title)
			for field in publication_headers[1:-1]:
				setattr(publication, field, getattr(pub_row, field))
			if len(pub_row.publication_type) > 0:
				publication.publication_type = PublicationType.objects.get(category=pub_row.publication_type)
			publication.save(save_user=user)
			messages += [f'{publication.title} {" created" if created else " updated. "}']
	return '\n'.join(messages)
	
def find_publication(fields):
	candidate_publications = Publication.objects.all()
	for word in fields:
		candidate_publications = candidate_publications.filter(Q(title__contains=word) | Q(first_author__contains=word) | Q(year__contains=word) | Q(journal__contains=word))
	return candidate_publications.get()

publication_sample_assign_headers = ['sample_id', 'publication', 'paper_individual_id', 'paper_group_label']
def publication_sample_assign(batch_file, user):
	messages = []
	with transaction.atomic():
		for row in spreadsheet_pass(batch_file):
			row_obj = row.spreadsheet_row_to_obj()
			sample = Sample.objects.get(reich_lab_id=reich_sample_number(row_obj.sample_id))
			publication = find_publication(row_obj.publication.split())
			pairing, created = PublicationLabels.objects.get_or_create(sample=sample, publication=publication)
			if len(row_obj.paper_individual_id) > 0:
				pairing.individual_id = row_obj.paper_individual_id
			if len(row_obj.paper_group_label) > 0:
				pairing.group_label = row_obj.paper_group_label
			messages += [f'{sample.reich_lab_id} was published in {publication.title}']
	return '\n'.join(messages)
	
