CREATE OR REPLACE VIEW samples_view AS
	SELECT *,
	'S' || TO_CHAR(reich_lab_id, 'FM99990000') AS sample_string
	FROM samples_sample;
	
CREATE OR REPLACE VIEW sequencing_run_shotgunanalysis_view AS
	SELECT *,
	(reads_mapped_hg19::decimal / raw_sequences) AS endogenous_fraction_from_raw
	FROM sequencing_run_shotgunanalysis;
