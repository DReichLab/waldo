import re
import sys
from samples.models import Library, Sample, Results
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

	library_list = Library.objects.filter(reich_lab_library_id__startswith='S{:d}.'.format(library_id.sample))
	
	#for x in library_list:
	#	print(x.reich_lab_library_id)
	
	if len(library_list) == 1:
		identifier = 'I{:d}'.format(library_id.sample)
	else:
		identifier = str(library_id)
	if damage_restricted: # retain whether damage restricted or not
		identifier += '_d'
	return identifier, library_id

def get_text(obj, field_name):
	if obj is not None:
		return getattr(obj, field_name)
	else:
		return ''

# get an named field from an object
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
def mod_append(thelist, string):
	if string != '':
		thelist.append(string)
	else:
		thelist.append(EMPTY)

# this library id may contain _d damage-restriction indicator
def library_anno_line(library_id_raw, sequencing_run_name, release_label):
	#print(library_id_raw, file=sys.stderr)
	instance_id, library_id_obj = individual_from_library_id(library_id_raw)
	library_id_str = str(library_id_obj)
	damage_restricted = library_id_raw.endswith('_d')
	try:
		sample = Sample.objects.get(reich_lab_id__exact=library_id_obj.sample)
	except Sample.DoesNotExist as e:
		# controls do not have sample information, but all regular samples should
		if len(library_id_obj.sample_suffix) == 0:
			print('{} not found'.format(library_id_obj.sample), file=sys.stderr)
			raise e
		sample = None
	
	fields = []
	
	#Instance ID ("_all" means includes a mix of UDG-treated and non-UDG-treated; "_published" distinguishes a published sample for a still-unpublished higher quality version)
	mod_append(fields, instance_id)
	
	#Master ID
	master_id = '' #TODO
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
	publication = ''
	mod_append(fields, publication)
	#Representative contact
	mod_append(fields, get_text(sample, 'collaborators'))
	#Completeness of Date Information
	mod_append(fields, get_text(sample, 'date_fix_flag'))
	#Average of 95.4% date range in calBP (defined as 1950 CE)
	mod_append(fields, get_number(sample, 'average_bp_date', 1))
	#Date: One of two formats. (Format 1) 95.4% CI calibrated radiocarbon age (Conventional Radiocarbon Age BP, Lab number) e.g. 5983-5747 calBCE (6980±50 BP, Beta-226472). (Format 2) Archaeological context date, e.g. 2500-1700 BCE
	mod_append(fields, get_text(sample, 'sample_date'))
	#Group_ID (format convention which we try to adhere to is "Country_<Geographic.Region_<Geographic.Subregion_>><Archaeological.Period.Or.DateBP_<Alternative.Archaeological.Period_>><Archaeological.Culture_<Alternative.Archaeological.Culture>><genetic.subgrouping.index.if.necessary_><"o_"sometimes.with.additional.detail.if.an.outlier><additional.suffix.especially.relative.status.if.we.recommend.removing.from.main.analysis.grouping><"contam_".if.contaminated><"lc_".if.<15000.SNPs.on.autosomal.targets><".SG".or.".DG".if.shotgun.data>; HG=hunter-gatherer, N=Neolithic, C=Chalcolithic/CopperAge, BA=BronzeAge, IA=IronAge, E=Early, M=Middle, L=Late, A=Antiquity)
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
	mod_append(fields, '1') # TODO
	
	results = Results.objects.get(library_id__exact = library_id_str, nuclear_seq_run__name__iexact = sequencing_run_name)
	nuclear = NuclearAnalysis.objects.get(parent = results, version_release = release_label, damage_restricted = damage_restricted)
	analysis_files = AnalysisFiles.objects.get(parent = results)
		
	try:
		mt = MTAnalysis.objects.get(parent = results, damage_restricted = damage_restricted)
	except MTAnalysis.DoesNotExist as e:
		mt = None
		if not damage-restricted: # when we do damage-restricted analysis, update
			print('{} MT not found, damage-restricted {}'.format(library_id_str, str(damage_restricted)), file=sys.stderr)
	
	try:
		shotgun = ShotgunAnalysis.objects.get(parent = results, damage_restricted = damage_restricted)
	except ShotgunAnalysis.DoesNotExist as e:
		shotgun = None
		if not damage-restricted: # when we do damage-restricted analysis, update
			print('{} shotgun not found, damage-restricted {}'.format(library_id_str, str(damage_restricted)), file=sys.stderr)
	
	#Data: mtDNA bam
	mod_append(fields, analysis_files.mt_bam)
	#Data: mtDNA fasta
	mod_append(fields, analysis_files.mt_fasta)
	#Data: pulldown logfile location
	mod_append(fields, analysis_files.pulldown_logfile_location)
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
	mod_append(fields, nuclear.sex)
	#Family ID and position within family
	mod_append(fields, '') # TODO
	#Y chrom. (automatically called only if >50000 autosomal SNPs hit)
	mod_append(fields, '') # TODO
	#mtDNA coverage (merged data)
	mod_append(fields, get_number(mt, 'coverage'))
	#mtDNA haplogroup if ≥2 coverage or published (merged data or consensus if not available)
	#mtDNA match to consensus if ≥2 coverage (merged data)
	if mt.coverage >= 2.0:
		mod_append(fields, get_text(mt, 'haplogroup'))
		mod_append(fields, get_number(mt, 'consensus_match'))
	else:
		mod_append(fields, '')
		mod_append(fields, '')
	#Damage rate in first nucleotide on sequences overlapping 1240k targets (merged data)
	mod_append(fields, get_number(nuclear, 'damage_last_base'))
	#Sex ratio [Y/(Y+X) counts] (merged data)
	x_hits = nuclear.x_hits
	y_hits = nuclear.y_hits
	try:
		sex_ratio = y_hits / (x_hits + y_hits)
		mod_append(fields, '{:.3f}'.format(sex_ratio))
	except:
		mod_append(fields, '-1')
	#Xcontam ANGSD SNPs (only if male and ≥200)
	#Xcontam ANGSD MOM point estimate (only if male and ≥200)
	#Xcontam ANGSD MOM Z-score (only if male and ≥200)
	#Xcontam ANGSD MOM 95% CI truncated at 0 (only if male and ≥200)
	if nuclear.sex == 'M':
		mod_append(fields, get_number(nuclear, 'angsd_snps', 0))
		if nuclear.angsd_snps >= 200:
			mod_append(fields, get_number(nuclear, 'angsd_mean'))
			mod_append(fields, get_number(nuclear, 'angsd_z'))
			angsd_se = nuclear.angsd_mean / nuclear.angsd_z
			angsd_min_range = max(0, nuclear.angsd_mean - 1.96 * angsd_se)
			angsd_max_range = nuclear.angsd_mean + 1.96 * angsd_se
			mod_append(fields, '[{:.3f}, {:.3f}]'.format(angsd_min_range, angsd_max_range)) # confidence interval
		else:
			for i in range(3):
				mod_append(fields, '')
	else:
		for i in range(4):
			mod_append(fields, '')
	#Library type (minus=no.damage.correction, half=damage.retained.at.last.position, plus=damage.fully.corrected, ss=single.stranded.library.preparation)
	library_type = Library.objects.get(reich_lab_library_id = library_id_str).udg_treatment
	if 'ss.half' not in library_type.lower():
		raise ValueError('Unexpected library type {}'.format(library_type))
	mod_append(fields, library_type)
	#LibraryID(s)
	mod_append(fields, '{}'.format(library_id_str))
	#endogenous by library (computed on shotgun data)
	mod_append(fields, get_number(shotgun, 'fraction_hg19', 5))
	# TODO by library changes (multiple libraries)
	#1240k coverage (by library)
	try:
		mod_append(fields, '{}'.format(get_number(nuclear, 'coverage_targeted_positions')))
	except:
		mod_append(fields, '')
	#Damage rate in first nucleotide on sequences overlapping 1240k targets (by library)
	mod_append(fields, '{}'.format(get_number(nuclear, 'damage_last_base')))
	#mtDNA coverage (by library)
	mod_append(fields, '{}'.format(get_number(mt, 'coverage')))
	#mtDNA haplogroup if ≥2 coverage (by library)
	#mtDNA match to consensus if ≥2 coverage (by library)
	if mt.coverage >= 2.0:
		mod_append(fields, '{}'.format(mt.haplogroup))
		#mod_append(fields, '{}'.format(get_number(mt, 'consensus_match')))
		mod_append(fields, '{}'.format(get_text(mt, 'consensus_match_95ci')))
	else:
		mod_append(fields, '')
		mod_append(fields, '')
	#batch notes (e.g. if a control well looks contaminated)
	mod_append(fields, '') # TODO not yet pulled in from ESS files
	
	#ASSESSMENT
	if damage_restricted:
		mod_append(fields, '')
	else:
		assessment_reasons = []
		assessment_snp = 0
		if nuclear.unique_snps_hit < 2500:
			assessment_snp = 2
			assessment_reasons.append('<2500.SNPs')
		elif nuclear.unique_snps_hit <= 5000:
			assessment_snp = 1
			assessment_reasons.append('2500.to.5000.SNPs')
		
		assessment_damage = 0
		if nuclear.damage_last_base < 0.03:
			assessment_damage = 2
		elif nuclear.damage_last_base < 0.10:
			assessment_damage = 1
		if assessment_damage > 0:
			assessment_reasons.append('damage.ss.half={:.3f}'.format(nuclear.damage_last_base))
		
		assessment_sex_ratio = 0
		if 0.1 <= sex_ratio and sex_ratio <= 0.3:
			assessment_sex_ratio = 2
		elif (0.03 <= sex_ratio and sex_ratio <= 0.1) or (0.3 <= sex_ratio and sex_ratio <= 0.35):
			assessment_sex_ratio = 1
		if assessment_sex_ratio > 0:
			assessment_reasons.append('sexratio[{:.3f}]'.format(sex_ratio))
		
		# (mtcontam 97.5th percentile estimates listed if coverage >2: <0.8 is "QUESTIONABLE_CRITICAL", 0.8-0.95 is "QUESTIONABLE", and 0.95-0.98 is recorded but "PASS", gets overriden by ANGSD)
		# TODO separate these lower and upper values so we do not have to reparse interval
		assessment_contammix = 0
		if mt.coverage >= 2.0:
			mtci = mt.consensus_match_95ci
			mtci_values = [float(v) for v in mtci[mtci.index('[')+1:mtci.index(']')-1].split(',')]
			mt_ci_upper = mtci_values[1]
			if mt_ci_upper < 0.8:
				assessment_contammix = 2
			elif mt_ci_upper < 0.95:
				assessment_contammix = 1
			if assessment_contammix > 0:
				assessment_reasons.append('mtmatchmax={:.3f}'.format(mt_ci_upper))
		
		#(Xcontam listed if |Z|>2 standard errors from zero: 0.02-0.05="QUESTIONABLE", >0.05="QUESTIONABLE_CRITICAL" or "FAIL") 
		assessment_angsd = 0
		if nuclear.sex == 'M' and nuclear.angsd_snps >= 200:
			if angsd_max_range >= 0.05:
				assessment_angsd = 2
			elif angsd_max_range >= 0.02:
				assessment_angsd = 1
			if assessment_angsd > 0:
				assessment_reasons.append('Xcontam=[{:.3f},{:.3f}]'.format(angsd_min_range, angsd_max_range))
			assessment_contammix = min(assessment_contammix, assessment_angsd) # angsd contamination will override mt contammix
		
		assessment_map = { 0 : 'PASS',
					1 : 'QUESTIONABLE',
					2 : 'QUESTIONABLE_CRITICAL' }
		assessment_overall = max(assessment_snp, assessment_damage, assessment_sex_ratio, assessment_contammix, assessment_angsd)
		
		assessment_reasons_str = ' ({})'.format(', '.join(assessment_reasons))
		assessment_string = '{}{}'.format(assessment_map[assessment_overall], assessment_reasons_str if assessment_overall > 0 else '')
		mod_append(fields, assessment_string)
	
	return fields
