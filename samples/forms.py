from django import forms
from django.forms import ModelChoiceField

from samples.models import PowderBatchStatus

import datetime

class IndividualForm(forms.Form):
	individual_id = forms.IntegerField(label='Reich Lab Individual ID') 

class LibraryIDForm(forms.Form):
	library_id = forms.CharField(max_length=20, min_length=7, label='Reich Lab Library ID')
	
class PowderBatchStatusSelect(ModelChoiceField):
	def label_from_instance(self, obj):
		return obj.description

class PowderBatchForm(forms.Form):
	name = forms.CharField(max_length=50)
	date = forms.DateField(initial=datetime.date.today)
	status = PowderBatchStatusSelect(queryset=PowderBatchStatus.objects.all().order_by('sort_order'), empty_label=None)
	notes = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 2})) 
