from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

import re

REGEX_WHITESPACE = re.compile(r'\s+')
def validate_no_whitespace(string):
	m = REGEX_WHITESPACE.search(string)
	if m is not None:
		raise ValidationError(_('Cannot contain whitespace')) 

REGEX_UNDERSCORE = re.compile(r'_')
def validate_no_underscore(string):
	m = REGEX_UNDERSCORE.search(string)
	if m is not None:
		raise ValidationError(_('Cannot contain underscore')) 
