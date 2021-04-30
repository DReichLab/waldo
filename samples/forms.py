from django import forms

class IndividualForm(forms.Form):
	individual_id = forms.IntegerField(label='Reich Lab Individual ID') 

class LibraryIDForm(forms.Form):
	library_id = forms.CharField(max_length=20, min_length=7, label='Reich Lab Library ID')

class PowderBatchForm(forms.Form):
	name = forms.CharField(max_length=50)
	notes = forms.CharField(required=False) 
