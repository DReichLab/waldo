import os.path
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
import datetime
from samples.models import CaptureLayout
from sequencing_run import library_id
from sequencing_run.assemble_libraries import output_bam_list
from sequencing_run.ssh_command import ssh_command
from sequencing_run.analysis import adna2_index_barcode_keys_used, index_barcode_keys_used, barcodes_set, i5_set, i7_set
from sequencing_run.models import SequencingAnalysisRun

class Command(BaseCommand):
	help = 'Create index barcode key file mapping to library ids from database for specified sequencing run'
	
	def add_arguments(self, parser):
		parser.add_argument('--library_file', required=True)
		parser.add_argument('--output_dir', required=True)
		parser.add_argument('--label', required=True)
		# parser.add_argument('--mysql_ibk', action='store_true')
		parser.add_argument('--no_header', action='store_true')
		
	def handle(self, *args, **options):
		library_file = os.path.abspath(options['library_file'])
		output_dir = os.path.abspath(options['output_dir'])
		# mysql_ibk = options['mysql_ibk']
		label = options['label']
		header = not(options['no_header'])

		demultiplex_path_head = '/n/groups/reich/matt/pipeline/demultiplex'
		nuclear_subdirectory = 'nuclear_aligned_unfiltered'
		mt_subdirectory = 'rsrs_aligned_filtered'

		# output dict format: {(library_id, index_barcode_key) : (seq_name, seq_date, experiment, nuclear_demultiplex_bam, mt_demultiplex_bam)}
		output_dict = {}

		with open(library_file, 'r') as f:
			for line in f:
				library = line.strip()
				library_queryset = CaptureLayout.objects.filter(library__reich_lab_library_id=library).exclude(capture_batch__protocol__name="Raw")
				# with open("{}/{}.index_barcode_map".format(output_dir, label)) as out:
				for result in library_queryset:
					# Try to grab indices and barcodes, make blank if not in database
					try:
						p5_index = result.p5_index.sequence
					except:
						p5_index = ''
					try:
						p7_index = result.p7_index.sequence
					except:
						p7_index = ''
					try:
						p5_barcode = result.library.p5_barcode.sequence
					except:
						p5_barcode = ''
					try:
						p7_barcode = result.library.p7_barcode.sequence
					except:
						p7_barcode = ''
					index_barcode_key = "_".join(p5_index, p7_index, p5_barcode, p7_barcode)
					experiment = result.capture_batch.protocol.name
					seq_name = result.sequencingrun.name
					seq_date = SequencingAnalysisRun.objects.filter(name=seq_name).first().sequencing_date.strftime('%Y%m%d')
					nuclear_demultiplex_bam = "/".join(demultiplex_path_head, "{}_{}".format(seq_date, seq_name), nuclear_subdirectory, index_barcode_key.replace(":", "-")) + ".bam"
					mt_demultiplex_bam = "/".join(demultiplex_path_head, "{}_{}".format(seq_date, seq_name), mt_subdirectory, index_barcode_key.replace(":", "-")) + ".bam"
					output_dict.update({(library_id, index_barcode_key) : (seq_name, seq_date, experiment, nuclear_demultiplex_bam, mt_demultiplex_bam)})
	
		with open("{}/{}.index_barcode_map".format(output_dir, label)) as out:
			if header:
				out.write("\t".join("library_id", "seq_name", "seq_date", "experiment", "index-barcode_key", "nuclear_bam_path", "mt_bam_path") + "\n")
			for key, value in output_dict.items():
				out.write("/t".join(key[0], value[0], value[1], value[2], key[1], value[3], value[4]))