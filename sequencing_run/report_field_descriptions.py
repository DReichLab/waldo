# This renders a web version of help for the screening pipeline report fields

def report_field_descriptions(request):
	report_fields = [
		("Index-Barcode Key", "The i5 index, i7 index, p5 barcode, and p7 barcode sequences are separated by _ characters: i5_i7_p5_p7. This is the key used to demultiplex, and it treats all barcodes in a Q barcode set as equivalent."),
		("sample_sheet_key", "This is the match in the sample sheet found to correspond to the demultiplexing key. This will differ from the Index-Barcode Key when a single component barcode is in the sample sheet instead of the four component barcodes."),
		("library_id", "The sample, extract and library identifiers as matched with the sample sheet using the sample_sheet_key"),
		("raw", "Number of paired reads matching index and barcodes with maximum 1 mismatch per index/barcode"),
		("merged", "Number of paired reads successfully merging with minimum overlap (currently 15 bases, some mismatch allowed). Only merged reads are aligned and used for further processing. Reads will fail to merge if < 30 base pairs. Maximum length is (76 * 2 - 15 (min overlap) - 2 * [barcode length]). For 7bp barcodes, max length is 123 base pairs."),
		("endogenous_pre", "The fraction of endogenous reads before deduplication. Equal to (autosome_pre + X_pre + Y_pre + MT_pre) / merged. This may be lower than earlier report versions, which counted all aligned reads, including those for decoys or unlocalized or unplaced contigs."),
		("autosome_pre", "Number of reads aligning to hs37d5 chromosomes 1-22 before deduplication"),
		("autosome_pre-coverage", "Sum of autosome read lengths normalized by autosome lengths before deduplication"),
		("autosome_post", "Number of reads aligning to hs37d5 chromosomes 1-22 after deduplication"),
		("autosome_post-coverage", "Sum of read lengths normalized by autosome lengths after deduplication"),
		("X_pre", "Number of reads aligning to hs37d5 X chromosome before deduplication"),
		("X_pre-coverage", "Sum of X chromosome read lengths normalized by X chromosome length before deduplication"),
		("X_post", "Number of reads aligning to hs37d5 X chromosome after deduplication"),
		("X_post-coverage", "Sum of X chromosome read lengths normalized by X chromosome length after deduplication"),
		("Y_pre", "Number of reads aligning to hs37d5 Y chromosome before deduplication"),
		("Y_pre-coverage", "Sum of Y chromosome read lengths normalized by Y chromosome length before deduplication"),
		("Y_post", "Number of reads aligning to hs37d5 Y chromosome after deduplication"),
		("Y_post-coverage", "Sum of Y chromosome read lengths normalized by Y chromosome length after deduplication"),
		("duplicates_hs37d5", "Number of duplicates for reads aligning to hs37d5 reference"),
		("median_hs37d5", "Median length of reads aligning to hs37d5 reference"),
		("mean_hs37d5", "Mean length of reads aligning to hs37d5 reference"),
		("damage_hs37d5_ct1", "Damage at first base for reads aligning to hs37d5 reference. Estimated by C->T transitions using PMD Tools"),
		("damage_hs37d5_ct2", "Damage at second base for reads aligning to hs37d5 reference. Estimated by C->T transitions using PMD Tools"),
		("damage_hs37d5_ga1", "Damage at first base for reads aligning to hs37d5 reference. Estimated by G->A transitions using PMD Tools"),
		("damage_hs37d5_ga2", "Damage at second base for reads aligning to hs37d5 reference. Estimated by G->A transitions using PMD Tools"),
		("MT_pre", "Number of reads aligning to rsrs MT reference before deduplication "),
		("MT_pre-coverage", "Sum of MT read lengths normalized by MT length before deduplication"),
		("MT_post", "Number of reads aligning to rsrs MT reference after deduplication"),
		("MT_post-coverage", "Sum of MT read lengths normalized by MT length after deduplication"),
		("duplicates_rsrs", "Number of duplicates for reads aligning to rsrs MT reference"),
		("median_rsrs", "Median length of reads aligning to rsrs MT reference"),
		("mean_rsrs", "Mean length of reads aligning to rsrs MT reference"),
		("damage_rsrs_ct1", "Damage at first base for reads aligning to rsrs MT. Estimated by C->T transitions using PMD Tools"),
		("damage_rsrs_ct2", "Damage at second base for reads aligning to rsrs MT. Estimated by C->T transitions using PMD Tools"),
		("damage_rsrs_ga1", "Damage at first base for reads aligning to rsrs MT. Estimated by G->A transitions using PMD Tools"),
		("damage_rsrs_ga2", "Damage at second base for reads aligning to rsrs MT. Estimated by G->A transitions using PMD Tools"),
		("Haplogroup", "MT haplogroup as determined by haplogrep using consensus variant calling"),
		("Haplogroup_rank", "The rank value is in the interval [0.5, 1] and indicates the quality of the haplogroup result. The value 0.5 is returned when there are no MT reads. The value 1 indicates a perfect match. "),
		#("spike3k_pre_autosome", "Number of reads overlapping a spike 3K target region on chromosome 1-22 before deduplication. For position p, this is the interval [p-50,p+50]."),
		#("spike3k_pre_x", "Number of reads overlapping a spike 3K target region on X chromosome before deduplication. For position p, this is the interval [p-50,p+50]."),
		#("spike3k_pre_y", "Number of reads overlapping a spike 3K target region on Y chromosome before deduplication. For position p, this is the interval [p-50,p+50]."),
		#("spike3k_post_autosome", "Number of reads overlapping a spike 3K target region on chromosome 1-22 after deduplication. For position p, this is the interval [p-50,p+50]."),
		#("spike3k_post_x", "Number of reads overlapping a spike 3K target region on X chromosome after deduplication. For position p, this is the interval [p-50,p+50]."),
		#("spike3k_post_y", "Number of reads overlapping a spike 3K target region on Y chromosome after deduplication. For position p, this is the interval [p-50,p+50]."),
		#("spike3k_post_sex", "Sex as determined by spike3k counts\nF if >= 50 autosomal hits and Y/Aut < 0.01,\nM if >= 50 autosomal hits and Y/Aut >= 0.05,\nU otherwise"),
		#("spike3k_complexity", "Library complexity as estimated by Nick Patterson's sppred3000 tool using the spike3k counts both before and after deduplication"),
		("contamination_contammix", "estimated maximum a posterior proportion authentic from contammix, using rsrs reads downsampled to 50x MT coverage"),
		("contamination_contammix_lower", "2.5%  credible quantile for proportion authentic"),
		("contamination_contammix_upper", "97.5%  credible quantile for proportion authentic"),
		("contamination_contammix_gelman", "Gelman and Rubin diagnostic [potential scale reduction factor] point estimate"),
		("contamination_contammix_inferred_error", "estimated error rate"),
		
		("preseq_target_coverage_at_threshold_", "ratio of unique reads hitting 1240k autosome targets to number of autosome targets")
    ]
	return report_fields
