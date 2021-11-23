from django.db import models

from datetime import datetime

from django.core.validators import RegexValidator

# This is the download of a (HiSeq X10) flowcell from the Broad Institute
# wget downloads asynchronously with these credentials
class FlowcellDownload(models.Model):
	STARTED = 0
	CHECKED = 1
	
	DOWNLOAD_STATES = (
		(STARTED, 'download started'),
		(CHECKED, 'checked')
	)
	alphanumeric = RegexValidator(r'^[0-9a-zA-Z]*$', 'Only alphanumeric characters are allowed.')
	
	name = models.CharField(max_length=20, unique=True, validators=[alphanumeric])
	password = models.CharField(max_length=20, validators=[alphanumeric])
	status = models.IntegerField(default=0, choices=DOWNLOAD_STATES)
	start_time = models.DateTimeField(default=datetime.now)
