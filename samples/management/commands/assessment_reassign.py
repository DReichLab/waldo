from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.auth.models import User
from samples.models import AssessmentCategory
from sequencing_run.models import NuclearAnalysis, GeneticAnalysis

class Command(BaseCommand):
	help = 'Replace an assessment category with another, and delete the category replaced'
	
	def add_arguments(self, parser):
		parser.add_argument('-r', '--to_replace', required=True, help='Replace this assessment category')
		parser.add_argument('-w', '--with', required=True, help='With this assessment category')
		parser.add_argument('-n', '--notes', help='Prepend assessment notes with this')
		parser.add_argument('-u', '--login_user', required=True, help='For modification tracking')
		
	def handle(self, *args, **options):
		user = User.objects.get(username=options['login_user'])
		with transaction.atomic():
			to_replace_category = AssessmentCategory.objects.get(category=options['to_replace'])
			with_category = AssessmentCategory.objects.get(category=options['with'])
			
			for x in NuclearAnalysis.objects.filter(assessment=to_replace_category):
				x.assessment = with_category
				if options['notes']:
					x.assessment_notes = options['notes'] + '; ' + x.assessment_notes
				x.save(save_user=user)
				
			for x in GeneticAnalysis.objects.filter(assessment=to_replace_category):
				x.assessment = with_category
				if options['notes']:
					x.assessment_notes = options['notes'] + '; ' + x.assessment_notes
				x.save(save_user=user)
			
			if to_replace_category != with_category:
				to_replace_category.delete()
