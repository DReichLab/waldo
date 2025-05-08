from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db import transaction

from samples.models import ArchaeologicalAssemblage, Sample, RadiocarbonDatedSample

class Command(BaseCommand):
	help = '''Combine archaeological assemblages that have the same burial code'''
	
	def add_arguments(self, parser):
		parser.add_argument("ids", type=int, nargs='+', help='archaeological assemblages')
		parser.add_argument('-b', "--burial_code", required=True, help='Single burial code to combine')
		
	def handle(self, *args, **options):
		with transaction.atomic():
			assemblages_queryset = ArchaeologicalAssemblage.objects.filter(id__in=options['ids']).order_by('id')
		
			burial_code = options['burial_code']
			assemblages_queryset = assemblages_queryset.filter(burial_code=burial_code)
				
			if assemblages_queryset.count() > 1:
				master_copy = assemblages_queryset.first()
				assemblages = list(assemblages_queryset)
				
				for assemblage in assemblages[1:]:
					for sample in Sample.objects.filter(archaeological_assemblage=assemblage):
						sample.archaeological_assemblage = master_copy
						sample.save()
						self.stdout.write(f'Sample {sample.id} {assemblage.id} {assemblage.burial_code} replaced by {master_copy.id} {master_copy.burial_code}')
					for radiocarbon_dated_sample in RadiocarbonDatedSample.objects.filter(archaeological_assemblage=assemblage):
						radiocarbon_dated_sample.archaeological_assemblage = master_copy
						radiocarbon_dated_sample.save()
						self.stdout.write(f'RadiocarbonDatedSample {radiocarbon_dated_sample.id} {assemblage.id} {assemblage.burial_code} replaced by {master_copy.id} {master_copy.burial_code}')
					assemblage.delete()
			else:
				self.stdout.write('No entries changed.')
