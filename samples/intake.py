from django.db import transaction
import re
import sys
from samples.models import Sample, ArchaeologicalAssemblage, SitePhase, Location, parse_sample_string
from samples.spreadsheet import spreadsheet_pass

def reich_sample_number(s):
	try:
		sample_number, control = parse_sample_string(s)
		return sample_number
	except ValueError:
		return int(s)

sample_headers = ['sample_id', 'skeletal_code', 'site_name', 'site_phase_category', 'burial_code']
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
				
			try:
				site_phase = SitePhase.objects.get(site=site, category=row.site_phase_category)
			except SitePhase.DoesNotExist:
				site_phase = SitePhase()
				site_phase.site = site
				site_phase.category = row.site_phase_category
				site_phase.save(save_user=user)
				messages.append(f'created site phase {site.site}: {site_phase.category}')
			
			if sample.archaeological_assemblage:
				if sample.archaeological_assemblage.burial_code != row.burial_code:
					raise ValueError(f'{row.sample_id} already has burial code {sample.archaeological_assemblage.burial_code}. Did not replace with {row.burial_code}')
			else:
				try:
					arch_assemblage = ArchaeologicalAssemblage.objects.get(site_phase=site_phase, burial_code=row.burial_code)
				except ArchaeologicalAssemblage.DoesNotExist:
					arch_assemblage = ArchaeologicalAssemblage()
					arch_assemblage.burial_code = row.burial_code
					arch_assemblage.site_phase = site_phase
					messages.append(f'created archeological assemblage {site.site}: {site_phase.category} {arch_assemblage.burial_code}')
					arch_assemblage.save(save_user=user)
				sample.archaeological_assemblage = arch_assemblage
			sample.skeletal_code_renamed = row.skeletal_code
			sample.save(save_user=user)
				
	return '\n'.join(messages)
