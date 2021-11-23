from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

import datetime

from sequencing_run.assemble_libraries import flowcells_for_names
from sequencing_run.models import SequencingAnalysisRun, Flowcell

class Command(BaseCommand):
	help = 'inspect flowcells for name, and optionally add prior flowcells to a analysis sequencing run'
	
	def add_arguments(self, parser):
		parser.add_argument('-n', '--names', required=True, nargs='+', help='Find flowcells for these names')
		parser.add_argument('-d', '--date_string', help='only needed if adding prior flowcells to analysis run')
		parser.add_argument('-a', '--add_to', help='Analysis run entry name to add to')
		
	def handle(self, *args, **options):
		names = options['names']
		flowcell_text_ids = flowcells_for_names(names)	
		
		print(flowcell_text_ids)

		if options['add_to'] and options['date_string']:
			date_string = options['date_string']
			date = datetime.datetime.strptime(date_string, "%Y%m%d").date()
			self.stdout.write(str(date))
			
			name_to_add_to = options['add_to']
			run_entry = SequencingAnalysisRun.objects.get(name = name_to_add_to, sequencing_date = date)
			self.stdout.write(str(run_entry))

			for flowcell_text_id in flowcell_text_ids:
				# uncompleted analyses show up with None flowcells
				# prevent uncompleted analyses from stopping new analysis
				if flowcell_text_id != None:
					run_entry.prior_flowcells_for_analysis.add(Flowcell.objects.get(flowcell_text_id=flowcell_text_id))
				run_entry.save()
