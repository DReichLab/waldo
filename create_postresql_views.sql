CREATE OR REPLACE VIEW samples_view AS
	SELECT *,
	'S' || TO_CHAR(reich_lab_id, 'FM99990000') AS sample_string
	FROM samples_sample;
	
CREATE OR REPLACE VIEW sequencing_run_shotgunanalysis_view AS
	SELECT *,
	(reads_mapped_hg19::decimal / raw_sequences) AS endogenous_fraction_from_raw
	FROM sequencing_run_shotgunanalysis;

CREATE OR REPLACE VIEW extract_used_total AS
	SELECT samples_library.extract_id_id,
	sum(samples_library.ul_extract_used) AS total_extract
	FROM samples_library
	GROUP BY samples_library.extract_id_id;

CREATE OR REPLACE VIEW lysate_used_total AS
	SELECT samples_extract.lysate_id_id,
	sum(samples_extract.lysis_volume_extracted) AS total_lysate_extracted
	FROM samples_extract
	GROUP BY samples_extract.lysate_id_id;

CREATE OR REPLACE VIEW powder_used_total AS
	SELECT samples_lysate.powder_sample_id,
	sum(samples_lysate.powder_used_mg) AS total_powder_lysed
	FROM samples_lysate
	GROUP BY samples_lysate.powder_sample_id;
