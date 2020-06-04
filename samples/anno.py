import re
import sys
from samples.models import Library, Sample, Results, Collaborator
from sequencing_run.models import AnalysisFiles, MTAnalysis, ShotgunAnalysis, NuclearAnalysis
from sequencing_run.library_id import LibraryID

def individual_from_library_id(library_id_raw):
	# Is there a prior library from this sample
	# No. Then we don't know whether individual matches any prior individual until we perform genetic analysis
	# Yes. Then there is an existing individual
	# retain whether damage restricted or not
	if library_id_raw.endswith('_d'):
		damage_restricted = True
		library_id_raw = library_id_raw.replace('_d','')
	else:
		damage_restricted = False
	library_id = LibraryID(library_id_raw)

	library_list = Library.objects.filter(reich_lab_library_id__startswith='S{:04d}.'.format(library_id.sample))
	
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

# this library id may contain _d damage-restriction indicator
def library_anno_line(instance_id_raw, sequencing_run_name, release_label, component_library_ids=[]):
	#print(instance_id_raw, file=sys.stderr)
	damage_restricted = instance_id_raw.endswith('_d')
	is_merge = len(component_library_ids) > 0
	if not is_merge: # single library
		instance_id, library_id_obj = individual_from_library_id(instance_id_raw)
		component_library_ids[0] = str(library_id_obj)
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
	
	#Skeletal code
	#mod_append(fields, get_text(sample, 'skeletal_code_renamed'))
	mod_append(fields, get_text(sample, 'skeletal_code'))
	#Skeletal element
	mod_append(fields, get_text(sample, 'skeletal_element'))
	#Year this sample was first published [missing: GreenScience 2010 (Vi33.15, Vi33.26), Olalde2018 (I2657), RasmussenNature2010 (Australian)]
	published_year = ''
	mod_append(fields, str(published_year))
	#Publication
	publication = 'Unpublished'
	mod_append(fields, publication)
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
	mod_append(fields, get_number(sample, 'average_bp_date', 0))
	#Date: One of two formats. (Format 1) 95.4% CI calibrated radiocarbon age (Conventional Radiocarbon Age BP, Lab number) e.g. 5983-5747 calBCE (6980±50 BP, Beta-226472). (Format 2) Archaeological context date, e.g. 2500-1700 BCE
	mod_append(fields, get_text(sample, 'sample_date'))
	#Group_ID (format convention which we try to adhere to is "Country_<Geographic.Region_<Geographic.Subregion_>><Archaeological.Period.Or.DateBP_<Alternative.Archaeological.Period_>><Archaeological.Culture_<Alternative.Archaeological.Culture>><genetic.subgrouping.index.if.necessary_><"o_"sometimes.with.additional.detail.if.an.outlier><additional.suffix.especially.relative.status.if.we.recommend.removing.from.main.analysis.grouping><"contam_".if.contaminated><"lc_".if.<15000.SNPs.on.autosomal.targets><".SG".or.".DG".if.shotgun.data>; HG=hunter-gatherer, N=Neolithic, C=Chalcolithic/CopperAge, BA=BronzeAge, IA=IronAge, E=Early, M=Middle, L=Late, A=Antiquity)
	if is_control:
		mod_append(fields, 'Control')
	else:
		mod_append(fields, get_text(sample, 'group_label'))
	#Locality
	mod_append(fields, get_text(sample, 'locality'))
	#Country
	mod_append(fields, get_text(sample, 'country'))
	#Lat.
	mod_append(fields, get_text(sample, 'latitude'))
	#Long
	mod_append(fields, get_text(sample, 'longitude'))
	#Data type
	mod_append(fields, '1240K') # TODO
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
			except Results.MultipleObjectsReturned as e:
				print('{} has multiple results'.format(library_id_str), file=sys.stderr)
				multiple_results = Results.objects.filter(library_id__exact = library_id_str).order_by('creation_timestamp')
				for result in multiple_results:
					print('sequencing runs: {}'.format(result.nuclear_seq_run.name), file=sys.stderr)
				results = multiple_results[len(multiple_results)-1]
				#raise e
		if release_label is not None:
			nuclear = NuclearAnalysis.objects.get(parent = results, version_release = release_label, damage_restricted = damage_restricted)
		else:
			try:
				nuclear = NuclearAnalysis.objects.get(parent = results,	damage_restricted = damage_restricted)
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
	analysis_files = AnalysisFiles.objects.get(parent = results) # TODO
	
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
	#mtDNA match to consensus if ≥2 coverage (merged data)
	if mt is not None and mt.coverage is not None and mt.coverage >= 2.0:
		mod_append(fields, get_text(mt, 'haplogroup'))
		mod_append(fields, reformat_interval(get_text(mt, 'consensus_match_95ci')))
	else:
		mod_append(fields, 'n/a (<2x coverage)')
		mod_append(fields, 'n/a (<2x coverage)')
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
	#mtDNA match to consensus if ≥2 coverage (by library)
	consensus_match_by_library = [reformat_interval(get_text(mt, 'consensus_match_95ci')) if (mt is not None and mt.coverage is not None and mt.coverage >= 2.0) else 'n/a (<2x coverage)' for mt in mt_list]
	mod_append(fields, ','.join(consensus_match_by_library))
	#batch notes (e.g. if a control well looks contaminated)
	mod_append(fields, '') # TODO not yet pulled in from ESS files

	if is_merge: # TODO kluge to output merge data
		return fields
	
	#ASSESSMENT
	assessment_reasons = []
	assessment_snp = 0
	if nuclear.unique_snps_hit < 500:
		assessment_snp = 3
		assessment_reasons.append('<500.SNPs')
	elif nuclear.unique_snps_hit < 2500:
		assessment_snp = 2
		assessment_reasons.append('<2500.SNPs')
	elif nuclear.unique_snps_hit <= 5000:
		assessment_snp = 1
		assessment_reasons.append('2500.to.5000.SNPs')
		
	assessment_damage = 0
	try:
		# single stranded damage has different thresholds than double stranded
		if library_type == 'half': # double stranded
			if nuclear.damage_last_base < 0.01:
				assessment_damage = 3
			elif nuclear.damage_last_base < 0.03:
				assessment_damage = 1
		elif 'ss' in library_type or 'minus' in library_type:
			if nuclear.damage_last_base < 0.03:
				assessment_damage = 3
			elif nuclear.damage_last_base < 0.10:
				assessment_damage = 1
		else:
			raise ValueError('unhandled library type: {}'.format(library_type))
		
		if assessment_damage > 0:
			assessment_reasons.append('damage.{}={:.3f}'.format(library_type, nuclear.damage_last_base))
	except:
		pass
		
	assessment_sex_ratio = 0
	try:
		if sex_ratio == -1:
			pass
		else:
			if (0.1 <= sex_ratio and sex_ratio <= 0.3):
				assessment_sex_ratio = 3
			elif (0.03 <= sex_ratio and sex_ratio <= 0.1) or (0.3 <= sex_ratio and sex_ratio <= 0.35):
				assessment_sex_ratio = 1
			if assessment_sex_ratio > 0:
				sex_ratio_str = 'sexratio={:.3f}'.format(sex_ratio)
				assessment_reasons.append(sex_ratio_str)
	except:
		pass
		
	# (mtcontam 97.5th percentile estimates listed if coverage >2: <0.8 is "QUESTIONABLE_CRITICAL", 0.8-0.95 is "QUESTIONABLE", and 0.95-0.98 is recorded but "PASS", gets overriden by ANGSD)
	# TODO separate these lower and upper values so we do not have to reparse interval
	assessment_contammix = 0
	try:
		if mt is not None and mt.coverage is not None and mt.coverage >= 2.0:
			mtci = mt.consensus_match_95ci
			mtci_values = [float(v) for v in mtci[mtci.index('[')+1:mtci.index(']')-1].split(',')]
			mt_ci_lower = mtci_values[0]
			mt_ci_upper = mtci_values[1]
			if mt_ci_upper < 0.9:
				assessment_contammix = 2
			elif mt_ci_upper < 0.98:
				assessment_contammix = 1
			if assessment_contammix > 0:
				assessment_reasons.append('mtcontam=[{:.3f},{:.3f}]'.format(mt_ci_lower, mt_ci_upper))
	except:
		pass
		
	#(Xcontam listed if |Z|>2 standard errors from zero: 0.02-0.05="QUESTIONABLE", >0.05="QUESTIONABLE_CRITICAL" or "FAIL") 
	assessment_angsd = 0
	try:
		if nuclear.sex == 'M' and nuclear.angsd_snps >= 200 and angsd_z > 2:
			if angsd_min_range > 0.1:
				assessment_angsd = 3
			elif angsd_min_range >= 0.05:
				assessment_angsd = 2
			elif angsd_min_range >= 0.02:
				assessment_angsd = 1
			# always print 
			assessment_reasons.append('Xcontam=[{:.3f},{:.3f}]'.format(angsd_min_range, angsd_max_range))
			assessment_contammix = min(assessment_contammix, assessment_angsd) # angsd contamination will override mt contammix
	except:
		pass
		
	assessment_map = { 0 : 'PASS',
				1 : 'QUESTIONABLE',
				2 : 'QUESTIONABLE_CRITICAL',
				3 : 'QUESTIONABLE_CRITICAL' } # David switched fails back to this category
	assessment_overall = max(assessment_snp, assessment_damage, assessment_sex_ratio, assessment_contammix, assessment_angsd)
	
	assessment_reasons_str = ' ({})'.format(', '.join(assessment_reasons))
	assessment_string = 'PROVISIONAL_{}{}'.format(assessment_map[assessment_overall], assessment_reasons_str if assessment_overall > 0 else '')
	if is_control:
		assessment_string = 'IGNORE_CONTROL'
	mod_append(fields, assessment_string)
	
	return fields
