import re
import sys
from django.db.models import Min, Q

from samples.models import Library, Sample, Results, Collaborator, get_value, RadiocarbonDatedSample, PublicationLabels, DataFileAssignment
from sequencing_run.models import AnalysisFiles, MTAnalysis, ShotgunAnalysis, NuclearAnalysis, GeneticAnalysis, FamilyRelationship
from sequencing_run.library_id import LibraryID

def library_list_from_library_id(library_id_raw):
	if library_id_raw.endswith('_d'):
		damage_restricted = True
		library_id_raw = library_id_raw.replace('_d','')
	else:
		damage_restricted = False
	library_id = LibraryID(library_id_raw)

	library_list = Library.objects.filter(reich_lab_library_id__startswith='S{:04d}.'.format(library_id.sample))
	return library_id, library_list, damage_restricted

def individual_from_library_id(library_id_raw):
	# Is there a prior library from this sample
	# No. Then we don't know whether individual matches any prior individual until we perform genetic analysis
	# Yes. Then there is an existing individual
	# retain whether damage restricted or not
	library_id, library_list, damage_restricted = library_list_from_library_id(library_id_raw)
	
	#for x in library_list:
	#	print(x.reich_lab_library_id)
	
	if len(library_list) == 1:
		identifier = 'I{:04d}'.format(library_id.sample)
	else:
		identifier = str(library_id)
	if damage_restricted: # retain whether damage restricted or not
		identifier += '_d'
	return identifier, library_id

# get a named field from an object
def get_text(obj, field_name):
	if obj is not None:
		return getattr(obj, field_name)
	else:
		return ''

# get a named number field from an object as a string
def get_number(obj, field_name, decimal_digits=3):
	if obj is not None:
		try:
			value = getattr(obj, field_name)
			return '{:.{precision}f}'.format(value, precision=decimal_digits)
		except (ValueError, TypeError) as e:
			pass
	return ''

# append a string to thelist, replacing blanks with '..'
EMPTY = '..'
def mod_append(thelist, string, default=EMPTY):
	if string != '':
		thelist.append(string)
	else:
		thelist.append(default)
		
def clean_string(value, default=EMPTY):
	if value is not None:
		value = value.replace('\r', '').replace('\n', '')
	return value if (value != '' and value is not None) else default

def replace_empty(thelist):
	return [s if len(s) > 0 else EMPTY for s in thelist]

def reformat_interval(interval_string):
	new_interval_string = ''
	try:
		values = [float(s) for s in interval_string.strip(' []').split(',')]
		new_interval_string = '[{:.3f},{:.3f}]'.format(values[0], values[1])
	except error:
		print(error, file=sys.stderr)
	finally:
		return new_interval_string
		
# return string representing anno file skeletal code column based on all of the underlying fields
def skeletal_code(sample):
	# Build a string like "collaborator_code (skeletal_code, accession_number, burial_code, burial_subcode)"
	# But, with no blanks and no repeated information
	skeletal_code = get_text(sample, 'skeletal_code')
	collaborator_code = get_text(sample, 'collaborator_code')
	accession_number = get_text(sample, 'accession_number')
	burial_code = get_value(sample, 'archaeological_assemblage', 'burial_code')
	burial_subcode = get_value(sample, 'burial_subcode')
	# ordering of Pinhasi elements is different
	if get_value(sample, 'collaborator', 'last_name') == 'Pinhasi' and get_value(sample, 'collaborator', 'first_name'):
		skeletal_code_possible_name_elements = [burial_code, collaborator_code, skeletal_code, accession_number, burial_subcode]
	else:
		skeletal_code_possible_name_elements = [collaborator_code, skeletal_code, accession_number, burial_code, burial_subcode]
	skeletal_code_name_elements = []
	for candidate in skeletal_code_possible_name_elements:
		if candidate is not None and len(candidate) > 0: # not empty
			add = True
			for index, element in enumerate(skeletal_code_name_elements): # check for duplicate info
				if candidate in element: # no new info
					add = False
					break
				if element in candidate: # superset of existing info, replace
					add = False
					skeletal_code_name_elements[index] = candidate
					break
			if add:
				skeletal_code_name_elements.append(candidate)
	skeletal_code_final = ''
	if len(skeletal_code_name_elements) >= 1:
		skeletal_code_final = skeletal_code_name_elements[0]
	if len(skeletal_code_name_elements) > 1:
		skeletal_code_final += f' ({", ".join(skeletal_code_name_elements[1:])})'
	return skeletal_code_final
	
def skeletal_element(sample):
	skeletal_element_category = get_value(sample, 'skeletal_element_category', 'category')
	skeletal_element_freeform = get_text(sample, 'skeletal_element')
	skeletal_element_text = skeletal_element_category + (f' ({skeletal_element_freeform})' if len(skeletal_element_freeform) > 0 else '')
	return skeletal_element_text
	
def morphological(sample):
	morphological_sex = get_text(sample, 'morphological_sex') # three db fields to build anno file entry from
	morphological_age = get_text(sample, 'morphological_age')
	morphological_age_range = get_text(sample, 'morphological_age_range')
	if morphological_age_range and not morphological_age_range.endswith('mos'):
		morphological_age_range += ' yrs' # add " yrs" to end if not listed explicitly in months
	morphological_column_elements = [morphological_age, morphological_age_range, morphological_sex]
	return '; '.join(filter(None, morphological_column_elements))
	
# return (file path, list of read groups)
def get_single_file_and_read_groups(genetic_analysis, file_type_str):
	files = {}
	assignments = DataFileAssignment.objects.filter(collection=genetic_analysis.data_instance, data_file__file_type__name=file_type_str)
	for data_file_assignment in assignments:
		if data_file_assignment.data_file.path not in files:
			files[data_file_assignment.data_file.path] = []
		read_group = data_file_assignment.read_group
		if len(read_group) > 0:
			files[data_file_assignment.data_file.path].append(data_file_assignment.read_group)
		
	if len(files) == 0:
		return '', []
	elif len(files) == 1:
		key = list(files.keys())[0]
		return key, files[key]
	else:
		raise NotImplementedError()

def get_single_file(genetic_analysis, file_type_str):
	single_file, read_groups = get_single_file_and_read_groups(genetic_analysis, file_type_str)
	return single_file
	
def get_read_groups(genetic_analysis):
	single_file, read_groups = get_single_file_and_read_groups(genetic_analysis, 'autosomal bam')
	return read_groups

# return string
def hetfa_ranfa_readgroups(genetic_analysis):
	hetfa = get_single_file(genetic_analysis, 'hetfa')
	ranfa = get_single_file(genetic_analysis, 'ranfa')
	read_groups = get_read_groups(genetic_analysis)
	values = (1 if len(hetfa) > 0 else 0) + (1 if len(ranfa) > 0 else 0) + (1 if len(read_groups) > 0 else 0)
	if values > 1:
		raise ValueError(f'Too many elements for hetfa/ranfa/readgroups {genetic_analysis.genetic_id}')
	elif len(hetfa) > 0:
		return hetfa
	elif len(ranfa) > 0:
		return ranfa
	else:
		return ':'.join(read_groups)
		
def family_representation(genetic_analysis):
	primary_sample = genetic_analysis.data_instance.primary_sample
	relations = FamilyRelationship.objects.filter(Q(person1__primary_sample=primary_sample) | Q(person2__primary_sample=primary_sample) ).filter(degree__gt=0).order_by('degree')
	relation_strings = []
	for relation in relations:
		relation_strings.append(str(relation))
	return ', '.join(relation_strings)

# subset of anno file fields relating to sample info, not analysis
# This is now obsolete. Use genetic_analysis_anno instead
def sample_anno(sample):
	fields = []
	#Skeletal code
	mod_append(fields, skeletal_code(sample))
	
	#Skeletal element
	mod_append(fields, skeletal_element(sample))
	#Year this sample was first published [missing: GreenScience 2010 (Vi33.15, Vi33.26), Olalde2018 (I2657), RasmussenNature2010 (Australian)]
	#Publication
	if len(sample.publications.all()) > 0:
		publications_ordered = sample.publications.all().order_by('-year')
		publication = ', '.join(p.abbreviation for p in publications_ordered)
		first_publication = publications_ordered.last()
		published_year = first_publication.year
		published_boolean = 1
		doi = first_publication.url
	else:
		publication = 'Unpublished'
		published_year = ''
		published_boolean = 0
		doi = ''
	
	mod_append(fields, str(published_boolean))
	mod_append(fields, str(published_year))
	mod_append(fields, publication)
	mod_append(fields, doi)
	#Representative contact
	if(sample is not None and sample.collaborator is not None):
		first_name = get_text(sample.collaborator, 'first_name')
		last_name = get_text(sample.collaborator, 'last_name')
		mod_append(fields, '{}, {}'.format(last_name, first_name))
	else:
		mod_append(fields, '')
	#Completeness of Date Information
	mod_append(fields, get_text(sample, 'date_fix_flag'))
	#Average of 95.4% date range in calBP (defined as 1950 CE)
	bp_date = get_number(sample, 'average_bp_date', 0)
	if bp_date == '':
		dates = sample.dates()
		if len(dates) > 0:
			bp_date = dates[0].date_bp
	mod_append(fields, bp_date)
	#Date: One of two formats. (Format 1) 95.4% CI calibrated radiocarbon age (Conventional Radiocarbon Age BP, Lab number) e.g. 5983-5747 calBCE (6980±50 BP, Beta-226472). (Format 2) Archaeological context date, e.g. 2500-1700 BCE
	mod_append(fields, get_text(sample, 'sample_date'))
	# Age at death, Morphological sex from physical anthropology
	mod_append(fields, morphological(sample))
	#Group_ID (format convention which we try to adhere to is "Country_<Geographic.Region_<Geographic.Subregion_>><Archaeological.Period.Or.DateBP_<Alternative.Archaeological.Period_>><Archaeological.Culture_<Alternative.Archaeological.Culture>><genetic.subgrouping.index.if.necessary_><"o_"sometimes.with.additional.detail.if.an.outlier><additional.suffix.especially.relative.status.if.we.recommend.removing.from.main.analysis.grouping><"contam_".if.contaminated><"lc_".if.<15000.SNPs.on.autosomal.targets><".SG".or.".DG".if.shotgun.data>; HG=hunter-gatherer, N=Neolithic, C=Chalcolithic/CopperAge, BA=BronzeAge, IA=IronAge, E=Early, M=Middle, L=Late, A=Antiquity)
	if sample.is_control():
		mod_append(fields, 'Control')
	else:
		mod_append(fields, get_value(sample, 'get_group_label'))
	#Locality
	locality = get_value(sample, 'location_str')
	mod_append(fields, locality)
	#Country
	country = sample.get_country() if sample else None
	mod_append(fields, get_text(country, 'country_name'))
	#Lat.
	mod_append(fields, get_value(sample, 'get_site', 'latitude') if sample else '')
	#Long
	mod_append(fields, get_value(sample, 'get_site', 'longitude') if sample else '')
	
	return fields
	
UNPUBLISHED = 'Unpublished'
# header strings
genetic_id_h = 'Genetic ID'
persistent_genetic_id_h = 'Persistent Genetic ID'
persistent_data_h = 'Persistent Data ID'
individual_id_h = 'Individual ID'
skeletal_code_h = 'Skeletal code'
skeletal_element_h = 'Skeletal element'
is_published_h = 'Is published'
pub_abbr_h = 'Publication abbreviation'
doi_h = 'DOI'
permanent_repo_h = 'Link to the most permanent repository hosting these data'
contact_h = 'Representative contact'
date_method_h = 'Method for Determining Date; unless otherwise specified, calibrations use 95.4% intervals from OxCal v4.4.2 Bronk Ramsey (2009); r5; Atmospheric data from Reimer et al (2020)'
date_bp_h = 'Date mean in BP in years before 1950 CE [OxCal mu for a direct radiocarbon date, and average of range for a contextual date]'
date_stdev_h = 'Date standard deviation in BP [OxCal sigma for a direct radiocarbon date, and standard deviation of the uniform distribution between the two bounds for a contextual date]'
date_full_h = 'Full Date One of two formats. (Format 1) 95.4% CI calibrated radiocarbon age (Conventional Radiocarbon Age BP, Lab number) e.g. 2624-2350 calBCE (3990±40 BP, Ua-35016). (Format 2) Archaeological context range, e.g. 2500-1700 calBCE'
morphological_h = 'Age at death, Morphological sex from physical anthropology'
group_id_h = 'Group ID'
locality_h = 'Locality'
political_entity_h = 'Political Entity'
latitude_h = 'Lat.'
longitude_h = 'Long.'
restrictions_h = 'Restrictions'
assessment_h = 'ASSESSMENT'
data_mt_bam = 'Data mtDNA bam'
data_mt_fasta = 'Data mtDNA fasta'
data_autosomal_bam_h = 'Data autosomal bam'
family_h = 'Family relations'
data_hetfa_ranfa_readgroups_h = 'Data autosomal readgroups or hetfa or ranfa'
	
def genetic_analysis_anno_headers():
	headers = [
		genetic_id_h,
		persistent_genetic_id_h,
		individual_id_h,
		skeletal_code_h,
		skeletal_element_h,
		is_published_h,
		pub_abbr_h,
		doi_h,
		permanent_repo_h,
		contact_h,
		date_method_h,
		date_bp_h,
		date_stdev_h,
		date_full_h,
		morphological_h,
		group_id_h,
		locality_h,
		political_entity_h,
		latitude_h,
		longitude_h,
		restrictions_h,
		persistent_data_h,
		data_mt_bam,
		data_mt_fasta,
		data_autosomal_bam_h,
		data_hetfa_ranfa_readgroups_h,
		family_h,
		assessment_h
	]
	return headers

def genetic_analysis_anno(genetic_analysis):
	sample = get_value(genetic_analysis, 'data_instance', 'primary_sample')
	
	fields = {}
	# Genetic ID
	fields[genetic_id_h] = genetic_analysis.genetic_id
	# Persistent 
	fields[persistent_genetic_id_h] = genetic_analysis.id
	fields[persistent_data_h] = genetic_analysis.data_instance.id
	# individual ID
	fields[individual_id_h] = sample.get_individual_id()
	
	#Skeletal code
	fields[skeletal_code_h] = skeletal_code(sample)
	
	#Skeletal element
	fields[skeletal_element_h] = skeletal_element(sample)
	
	#publication
	publication_labels = PublicationLabels.objects.filter(genetic_id_entry=genetic_analysis, publication__year__isnull=False).order_by('id')
	if publication_labels.count() > 0:
		is_published = 1
		publication_label = publication_labels[0]
	else:
		publication_label = None
		is_published = 0
	if publication_labels.count() > 1:
		print(f'Multiple publication labels for the same genetic id {genetic_analysis.genetic_id}\t{" ".join([str(p.id) for p in publication_labels])}', file=sys.stderr)

	fields[is_published_h] = str(is_published)
	fields[pub_abbr_h] = get_value(publication_label, 'publication', 'abbreviation', default=UNPUBLISHED)
	fields[doi_h] = get_value(publication_label, 'publication', 'url')
	fields[permanent_repo_h] = genetic_analysis.permanent_repository
	
	fields[contact_h] = get_value(sample, 'collaborator', 'get_name_last_first')
	fields[date_method_h] = get_value(sample, 'date_fix_flag')
	fields[date_bp_h] = get_number(sample, 'average_bp_date', 0)
	fields[date_stdev_h] = get_value(sample, 'date_stdev')
	fields[date_full_h] = get_value(sample, 'sample_date')
	fields[morphological_h] = morphological(sample)
	fields[group_id_h] = get_value(sample, 'get_group_label')
	fields[locality_h] = get_value(sample, 'location_str')
	fields[political_entity_h] = get_value(sample, 'get_country', 'country_name')
	fields[latitude_h] = get_value(sample, 'get_site', 'latitude', default='')
	fields[longitude_h] = get_value(sample, 'get_site', 'longitude', default='')
	fields[restrictions_h] = get_value(sample, 'special_restriction', 'description')
	
	fields[data_mt_bam] = get_single_file(genetic_analysis, 'MT bam')
	fields[data_mt_fasta] = get_single_file(genetic_analysis, 'MT fasta')
	fields[data_autosomal_bam_h] = get_single_file(genetic_analysis, 'autosomal bam')
	fields[data_hetfa_ranfa_readgroups_h] = hetfa_ranfa_readgroups(genetic_analysis)
	
	fields[family_h] = family_representation(genetic_analysis)
	
	fields[assessment_h] = get_value(genetic_analysis, 'assessment', 'category')
		
	# publications = PublicationLabels.objects.filter(Q(sample=sample) | Q(genetic_id_entry__data_instance__primary_sample=sample) ).distinct().order_by('publication__year')
	
	display_fields = { key : clean_string(str(value)) for key, value in fields.items() }
	return display_fields
	
def genetic_id_anno(genetic_id):
	genetic_analysis = GeneticAnalysis.objects.get(genetic_id=genetic_id)
	return genetic_analysis_anno(genetic_analysis)

# this library id may contain _d damage-restriction indicator
def library_anno_line(instance_id_raw, sequencing_run_name, release_label, component_library_ids=[], ignore_missing_analyses = False):
	#print(instance_id_raw, file=sys.stderr)
	damage_restricted = instance_id_raw.endswith('_d')
	is_merge = len(component_library_ids) > 0
	if not is_merge: # single library
		instance_id, library_id_obj = individual_from_library_id(instance_id_raw)
		component_library_ids = [str(library_id_obj)]
	else: # merge
		instance_id = instance_id_raw
		ignored, library_id_obj = individual_from_library_id(component_library_ids[0]) # assumes first library has sample number
	
	is_control = len(library_id_obj.sample_suffix) > 0
	try:
		sample = Sample.objects.get(reich_lab_id__exact=library_id_obj.sample, control__exact=library_id_obj.sample_suffix)
	except Sample.DoesNotExist as e:
		# controls do not have sample information, but all regular samples should
		if not is_control:
			print('{} not found'.format(library_id_obj.sample), file=sys.stderr)
			raise e
		sample = None
	
	fields = []
	
	fields.append('') # index
	#Instance ID ("_all" means includes a mix of UDG-treated and non-UDG-treated; "_published" distinguishes a published sample for a still-unpublished higher quality version)
	mod_append(fields, instance_id)
	
	#Master ID
	master_id = get_text(sample, 'individual_id')
	if is_merge:
		mod_append(fields, instance_id.split('_')[0])
	elif len(library_id_obj.sample_suffix) > 0: # controls do not have master ID
		mod_append(fields, '')
	else:
		mod_append(fields, master_id)
	
	fields += sample_anno(sample)
	
	#Data type
	mod_append(fields, 'Twist1.4M')
	#No. Libraries
	mod_append(fields, str(len(component_library_ids)))
	
	nuclear_list = []
	mt_list = []
	shotgun_list = []
	for library_id_str in component_library_ids:
		if sequencing_run_name is not None:
			results = Results.objects.get(library_id__exact = library_id_str, nuclear_seq_run__name__iexact = sequencing_run_name)
		else:
			try:
				results = Results.objects.get(library_id__exact = library_id_str)
			except (Results.DoesNotExist, Results.MultipleObjectsReturned) as e:
				if type(e) == Results.MultipleObjectsReturned:
					print('{} has multiple results'.format(library_id_str), file=sys.stderr)
					multiple_results = Results.objects.filter(library_id__exact = library_id_str).order_by('creation_timestamp')
					for result in multiple_results:
						print('sequencing runs: {}'.format(result.nuclear_seq_run.name), file=sys.stderr)
					results = multiple_results[len(multiple_results)-1]
				if type(e) == Results.DoesNotExist:
					if ignore_missing_analyses:
						print('{} has no results object'.format(library_id_str), file=sys.stderr)
						return fields
					raise e
				else:
					raise e
				#raise e
		if release_label is not None:
			nuclear = NuclearAnalysis.objects.get(parent = results, version_release = release_label, damage_restricted = damage_restricted)
		else:
			try:
				nuclear = NuclearAnalysis.objects.get(parent = results, damage_restricted = damage_restricted)
			except NuclearAnalysis.DoesNotExist as error:
				nuclear = None
				print('{} Nuclear analysis not found, damage-restricted {}'.format(library_id_str, str(damage_restricted)), file=sys.stderr)
			
		try:
			mt = MTAnalysis.objects.get(parent = results, damage_restricted = damage_restricted)
		except MTAnalysis.DoesNotExist as e:
			mt = None
			if not damage_restricted: # when we do damage-restricted analysis, update
				print('{} MT not found, damage-restricted {}'.format(library_id_str, str(damage_restricted)), file=sys.stderr)
		
		try:
			shotgun = ShotgunAnalysis.objects.get(parent = results, damage_restricted = damage_restricted)
		except ShotgunAnalysis.DoesNotExist as e:
			shotgun = None
			if not damage_restricted: # when we do damage-restricted analysis, update
				print('{} shotgun not found, damage-restricted {}'.format(library_id_str, str(damage_restricted)), file=sys.stderr)
		nuclear_list += [nuclear]
		mt_list += [mt]
		shotgun_list += [shotgun]
	try:
		analysis_files = AnalysisFiles.objects.get(parent = results) # TODO
	except AnalysisFiles.DoesNotExist as error:
		print('{} AnalysisFiles not found'.format(library_id_str), file=sys.stderr)
		if ignore_missing_analyses:
			return fields
		raise error
	
	#Data: mtDNA bam
	mod_append(fields, analysis_files.mt_bam)
	#Data: mtDNA fasta
	mod_append(fields, analysis_files.mt_fasta)
	#Data: pulldown logfile location
	mod_append(fields, nuclear.pulldown_logfile_location)
	#Data: pulldown sample ID
	mod_append(fields, analysis_files.pulldown_1st_column_nickdb)
	#Data: autosomal bam
	mod_append(fields, analysis_files.nuclear_bam)
	#Data: autosomal readgroups or hetfa or ranfa
	mod_append(fields, analysis_files.pulldown_5th_column_nickdb_readgroup_diploid_source)
	#Coverage on autosomal targets
	mod_append(fields, get_number(nuclear, 'coverage_targeted_positions'))
	#SNPs hit on autosomal targets
	mod_append(fields, get_number(nuclear, 'unique_snps_hit', 0))
	#Mean length of shotgun sequences (merged data)
	mod_append(fields, get_number(shotgun, 'mean_median_sequence_length', 1))
	#Sex
	mod_append(fields, nuclear.sex, 'U')
	#Family ID and position within family
	mod_append(fields, '') # TODO
	#Y chrom. (automatically called only if >50000 autosomal SNPs hit)
	mod_append(fields, '') # TODO
	#mtDNA coverage (merged data)
	mod_append(fields, get_number(mt, 'coverage'))
	#mtDNA haplogroup if ≥2 coverage or published (merged data or consensus if not available)
	if mt is not None and mt.coverage is not None and mt.coverage >= 2.0:
		mod_append(fields, get_text(mt, 'haplogroup'))
	else:
		mod_append(fields, 'n/a (<2x coverage)')
	#mtDNA match to consensus if ≥10 coverage (merged data)
	if mt is not None and mt.coverage is not None and mt.coverage >= 10.0:
		mod_append(fields, reformat_interval(get_text(mt, 'consensus_match_95ci')))
	else:
		mod_append(fields, 'n/a (<10x coverage)')
	#Damage rate in first nucleotide on sequences overlapping 1240k targets (merged data)
	mod_append(fields, get_number(nuclear, 'damage_last_base'))
	#Sex ratio [Y/(Y+X) counts] (merged data)
	x_hits = nuclear.x_hits
	y_hits = nuclear.y_hits
	try:
		sex_ratio = y_hits / (x_hits + y_hits)
		mod_append(fields, '{:.3f}'.format(sex_ratio))
	except:
		sex_ratio = -1
		mod_append(fields, '')
	#Xcontam ANGSD SNPs (only if male and ≥200)
	#Xcontam ANGSD MOM point estimate (only if male and ≥200)
	#Xcontam ANGSD MOM Z-score (only if male and ≥200)
	#Xcontam ANGSD MOM 95% CI truncated at 0 (only if male and ≥200)
	if nuclear.sex == 'M':
		mod_append(fields, get_number(nuclear, 'angsd_snps', 0))
		if nuclear.angsd_snps >= 200:
			mod_append(fields, get_number(nuclear, 'angsd_mean'))
			mod_append(fields, get_number(nuclear, 'angsd_z'))
			angsd_z = nuclear.angsd_z
			angsd_se = nuclear.angsd_mean / angsd_z
			angsd_min_range = max(0, nuclear.angsd_mean - 1.96 * angsd_se)
			angsd_max_range = nuclear.angsd_mean + 1.96 * angsd_se
			mod_append(fields, '[{:.3f},{:.3f}]'.format(angsd_min_range, angsd_max_range)) # confidence interval
		else:
			for i in range(3):
				mod_append(fields, 'n/a (<200 SNPs)')
	elif nuclear.sex == 'F':
		for i in range(4):
			mod_append(fields, 'n/a (female)')
	else:
		for i in range(4):
			mod_append(fields, 'n/a (unknown sex)')
	#Library type (minus=no.damage.correction, half=damage.retained.at.last.position, plus=damage.fully.corrected, ss=single.stranded.library.preparation)
	library_types = []
	for library_id_str in component_library_ids:
		library_obj = Library.objects.get(reich_lab_library_id = library_id_str)
		udg = library_obj.udg_treatment.lower()
		# partial = double-stranded, UDG half
		# USER = single-stranded, UDG half
		if udg == 'partial' or udg == 'USER':
			udg = 'half'
		strandedness = library_obj.library_type.lower()
		library_types += ['{}.{}'.format(strandedness, udg)]
		#if 'ss.half' not in library_type:
			#raise ValueError('Unexpected library type {}'.format(library_type))
	mod_append(fields, ','.join(library_types))
	#LibraryID(s)
	mod_append(fields, ','.join(component_library_ids))
	#endogenous by library (computed on shotgun data)
	endogenous_by_library = [get_number(shotgun, 'fraction_hg19', 5) for shotgun in shotgun_list]
	mod_append(fields, ','.join(replace_empty(endogenous_by_library)))
	#1240k coverage (by library)
	try:
		coverage_by_library = [get_number(nuclear, 'coverage_targeted_positions') for nuclear in nuclear_list]
		mod_append(fields, ','.join(replace_empty(coverage_by_library)))
	except:
		mod_append(fields, '')
	#Damage rate in first nucleotide on sequences overlapping 1240k targets (by library)
	damage_by_library = [get_number(nuclear, 'damage_last_base') for nuclear in nuclear_list]
	mod_append(fields, ','.join(replace_empty(damage_by_library)))
	#mtDNA coverage (by library)
	mt_coverage_by_library = [get_number(mt, 'coverage') for mt in mt_list]
	mod_append(fields, ','.join(replace_empty(mt_coverage_by_library)))
	#mtDNA haplogroup if ≥2 coverage (by library)
	haplogroup_by_library = [mt.haplogroup if (mt is not None and mt.coverage is not None and mt.coverage >= 2.0) else 'n/a (<2x coverage)' for mt in mt_list]
	mod_append(fields, ','.join(haplogroup_by_library))
	#mtDNA match to consensus if ≥10 coverage (by library)
	consensus_match_by_library = [reformat_interval(get_text(mt, 'consensus_match_95ci')) if (mt is not None and mt.coverage is not None and mt.coverage >= 10.0) else 'n/a (<10x coverage)' for mt in mt_list]
	mod_append(fields, ','.join(consensus_match_by_library))
	#batch notes (e.g. if a control well looks contaminated)
	mod_append(fields, '') # TODO not yet pulled in from ESS files

	if is_merge: # TODO kluge to output merge data
		return fields
	
	#ASSESSMENT
	assessment_reasons = []
	assessment_snp = 0
	if nuclear.unique_snps_hit < 500:
		assessment_snp = 4
		assessment_reasons.append('<500.SNPs')
	elif nuclear.unique_snps_hit < 2500:
		assessment_snp = 3
		assessment_reasons.append('<2500.SNPs')
	elif nuclear.unique_snps_hit <= 5000:
		assessment_snp = 2
		assessment_reasons.append('2500.to.5000.SNPs')
		
	assessment_damage = 0
	damage_assessment_list_anyway = False
	if len(component_library_ids) == 1:
		library_obj = Library.objects.get(reich_lab_library_id = library_id_str)
		udg = library_obj.udg_treatment.lower()
		library_type = library_obj.library_type.lower()
		# single stranded damage has different thresholds than double stranded
		if (library_type == 'ds') and ((udg == 'partial') or (udg == 'half') or (udg == 'user')) : # double stranded
			try:
				if nuclear.damage_last_base < 0.01:
					assessment_damage = 4
				elif nuclear.damage_last_base <= 0.03:
					assessment_damage = 1
					#damage_assessment_list_anyway = True
			except:
				pass
		elif 'ss' in library_type or 'minus' in udg:
			try:
				if nuclear.damage_last_base < 0.01:
					assessment_damage = 4
				elif nuclear.damage_last_base <= 0.03:
					assessment_damage = 2
				elif nuclear.damage_last_base <= 0.10:
					assessment_damage = 1
					#damage_assessment_list_anyway = True
			except:
				pass
		else:
			raise ValueError('unhandled library type: {} {}'.format(library_type, udg))
		
		if assessment_damage > 0 or damage_assessment_list_anyway == True:
			assessment_reasons.append('damage.{}={:.3f}'.format(library_type, nuclear.damage_last_base))
		
	assessment_sex_ratio = 0
	try:
		if sex_ratio == -1:
			pass
		else:
			if (0.1 <= sex_ratio and sex_ratio <= 0.3):
				assessment_sex_ratio = 4
			elif (0.03 <= sex_ratio and sex_ratio < 0.1) or (0.3 < sex_ratio and sex_ratio <= 0.32):
				assessment_sex_ratio = 2
			elif (0.02 <= sex_ratio and sex_ratio < 0.03) or (0.32 < sex_ration and sex_ration <= 0.33):
				assessment_sex_ratio = 1
			if assessment_sex_ratio > 0:
				sex_ratio_str = 'sexratio={:.3f}'.format(sex_ratio)
				assessment_reasons.append(sex_ratio_str)
	except:
		pass
		
	# (mtcontam 97.5th percentile estimates listed if coverage >2: <0.8 is "QUESTIONABLE_CRITICAL", 0.8-0.95 is "QUESTIONABLE", and 0.95-0.98 is recorded but "PASS", gets overriden by ANGSD)
	# TODO separate these lower and upper values so we do not have to reparse interval
	assessment_contammix = 0
	contammix_list_anyway = False
	try:
		if mt is not None and mt.coverage is not None and mt.coverage >= 10.0:
			mtci = mt.consensus_match_95ci
			mtci_values = [float(v) for v in mtci[mtci.index('[')+1:mtci.index(']')-1].split(',')]
			mt_ci_lower = mtci_values[0]
			mt_ci_upper = mtci_values[1]
			if mt_ci_upper < 0.9:
				assessment_contammix = 3
			elif mt_ci_upper <= 0.95:
				assessment_contammix = 2
			elif mt_ci_upper < 0.98:
				assessment_contammix = 1
			contammix_list_anyway = False
			if assessment_contammix > 0 or contammix_list_anyway == True:
				assessment_reasons.append('mtcontam=[{:.3f},{:.3f}]'.format(mt_ci_lower, mt_ci_upper))
	except:
		pass
		
	#(Xcontam listed if |Z|>2 standard errors from zero: 0.02-0.05="QUESTIONABLE", >0.05="QUESTIONABLE_CRITICAL" or "FAIL") 
	assessment_angsd = 0
	try:
		if nuclear.sex == 'M' and nuclear.angsd_snps >= 200: #and angsd_z > 2:
			if angsd_min_range > 0.02:
				assessment_angsd = 4
			elif angsd_min_range >= 0.01:
				assessment_angsd = 2
			elif angsd_min_range >= 0.005:
				assessment_angsd = 1
			if assessment_angsd > 0:
				assessment_reasons.append('ANGSD=[{:.3f},{:.3f}]'.format(angsd_min_range, angsd_max_range))
			if angsd_max_range < 0.01 and assessment_contammix == 2: # QUESTIONABLE status overriden if upper bound of angsd is <0.01
				assessment_contammix = min(assessment_contammix, assessment_angsd) # angsd contamination will override mt contammix
	except:
		pass
		
	assessment_map = { 0 : 'PASS',
				1 : 'PASS',
				2 : 'QUESTIONABLE',
				3 : 'CRITICAL',
				4 : 'CRITICAL' } # David switched fails back to this category
	assessment_overall = max(assessment_snp, assessment_damage, assessment_sex_ratio, assessment_contammix, assessment_angsd)
	
	assessment_reasons_str = ' ({})'.format(', '.join(assessment_reasons))
	assessment_string = 'PROVISIONAL_{}{}'.format(assessment_map[assessment_overall], assessment_reasons_str if assessment_overall > 0 else '')
	if is_control:
		assessment_string = 'IGNORE_CONTROL'
	mod_append(fields, assessment_string)
	
	return fields
