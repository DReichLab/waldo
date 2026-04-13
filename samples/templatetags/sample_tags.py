from django import template

register = template.Library()


@register.filter
def modifier_display(username, labels):
	"""Look up username in labels dict (initials if wetlab staff); empty shows em dash."""
	if not username:
		return '—'
	if not labels:
		return username
	return labels.get(username, username)
