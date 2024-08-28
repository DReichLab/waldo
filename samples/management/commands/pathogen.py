from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from samples.models import SequencingRun, SequencedLibrary
from sequencing_run.models import DemultiplexedSequencing

class Command(BaseCommand):
	help = "Find bams for samples for pathogen processing"
	
	def add_arguments(self, parser):
		parser.add_argument('-f', '--sample_file', help='Samples to find bams with unaligned reads from file, one per line')
		parser.add_argument("sample", nargs='*', help='Samples to find bams with unaligned reads')

	def handle(self, *args, **options):
		if options['sample']:
			for sample in options['sample']:
				self.pathogen_sample(sample)
		if options['sample_file']:
			with open(options['sample_file']) as f:
				for line in f:
					self.pathogen_sample(line.strip())

	def pathogen_sample(self, sample):
		#self.stdout.write(f'{sample}')
		sequenced_libraries = SequencedLibrary.objects.filter(indexed_library__library__sample__reich_lab_id=int(sample)).exclude(sequencing_run__reich_lab_release_version='')
		for sequenced_library in sequenced_libraries:
			sequencing_run = sequenced_library.sequencing_run.name
			i5 = sequenced_library.indexed_library.get_i5().sequence
			i7 = sequenced_library.indexed_library.get_i7().sequence
			p5 = sequenced_library.indexed_library.library.p5_barcode.sequence
			p7 = sequenced_library.indexed_library.library.p7_barcode.sequence
			index_barcode_combination = f'{i5}_{i7}_{p5}_{p7}'.replace(':', '-')
			demultiplexed = DemultiplexedSequencing.objects.filter(i5_index=i5, i7_index=i7, p5_barcode=p5, p7_barcode=p7, path__contains=sequencing_run).exclude( reference='rsrs').filter(path__contains=index_barcode_combination).filter(path__contains='unfiltered')

			library_id = sequenced_library.indexed_library.library.reich_lab_library_id
			experiment = sequenced_library.indexed_library.capture_batch.protocol.name

			for bam in demultiplexed:
				self.stdout.write(f'{library_id}\t{experiment}\t{sequencing_run}\t{bam.path}\t{bam.reference}')
