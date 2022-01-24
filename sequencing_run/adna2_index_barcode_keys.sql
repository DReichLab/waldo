select 
coalesce(samples_p5_index.sequence, '') || '_' || coalesce(samples_p7_index.sequence, '') || '_' || coalesce(p5_barcode_seq.sequence, '') || '_' || coalesce(p7_barcode_seq.sequence, '') as index_barcode_key,
coalesce(samples_library.reich_lab_library_id,
		 case
		 	when samples_controltype.control_type = 'PCR Negative' then 'Contl.PCR'
		 	when samples_controltype.control_type = 'Capture Positive' then 'Contl.Capture'
		 	else samples_controltype.control_type
		 end
		) as library_id,
-- sequencing_run_sequencinganalysisrun.name as seq_run_name,
-- sequencing_run_sequencinganalysisrun.sequencing_date as seq_run_date,
samples_captureorshotgunplate.name as plate_name,
	case
		when samples_captureprotocol.name like '%Twist%' then 'Twist1.4M'
		when samples_captureprotocol.name like '%1240k%' then '1240K+'
		else samples_captureprotocol.name
	end as experiment
from sequencing_run_sequencinganalysisrun
left join samples_sequencingrun on sequencing_run_sequencinganalysisrun.name = samples_sequencingrun.name
left join samples_sequencingrun_indexed_libraries on samples_sequencingrun.id = samples_sequencingrun_indexed_libraries.sequencingrun_id
left join samples_capturelayout on samples_sequencingrun_indexed_libraries.capturelayout_id = samples_capturelayout.id
left join samples_library on samples_capturelayout.library_id = samples_library.id
left join samples_barcode p5_barcode_seq on samples_library.p5_barcode_id = p5_barcode_seq.id
left join samples_barcode p7_barcode_seq on samples_library.p7_barcode_id = p7_barcode_seq.id
left join samples_p5_index on samples_capturelayout.p5_index_id = samples_p5_index.id
left join samples_p7_index on samples_capturelayout.p7_index_id = samples_p7_index.id
left join samples_controltype on samples_capturelayout.control_type_id = samples_controltype.id
left join samples_captureorshotgunplate on samples_capturelayout.capture_batch_id = samples_captureorshotgunplate.id
left join samples_captureprotocol on samples_captureorshotgunplate.protocol_id = samples_captureprotocol.id
where sequencing_run_sequencinganalysisrun.name = 'Tribe.27_SQ'
and sequencing_run_sequencinganalysisrun.sequencing_date = '2021-12-17'