from django.core.management.base import BaseCommand

import argparse

from samples.models import LibraryBatch, get_wetlab_staff


class Command(BaseCommand):
	help = "Assign extracts to a library batch from a tab-separated spreadsheet with headers Position and Extract (well positions, extract ids, library negatives, library positive, external samples as extracts)."

	def add_arguments(self, parser):
		parser.add_argument('library_batch_name')
		parser.add_argument('extract_layouts', type=argparse.FileType('rb'), help="Tab-separated file: header row must include Position and Extract columns")
		parser.add_argument('--library_ids', help='Allow existing library ids to stand in for their extracts', action='store_true')
		parser.add_argument('--controls', help='Add controls from control layout. Controls in explicit layout are always added and do not require this option.', action='store_true')
		parser.add_argument('--rotate_controls', action='store_true', help='Rotate controls from layout (non-explicit) as they are added to the plate')
		parser.add_argument('--user', nargs='+', help='Wetlab staff name')
		parser.add_argument('--rotate', action='store_true', help='Rotate new elements as they are added to the plate')

	def handle(self, *args, **options):
		library_batch = LibraryBatch.objects.get(name=options['library_batch_name'])
		user = None
		if options['user']:
			wetlab_user = get_wetlab_staff(options['user'])
			user = wetlab_user.login_user
		with options['extract_layouts'] as extract_layouts:
			library_batch.load_mob_layout(
				extract_layouts,
				user,
				library_ids=options['library_ids'],
				controls=options['controls'],
				rotate_controls=options['rotate_controls'],
				rotate=options['rotate'],
			)
