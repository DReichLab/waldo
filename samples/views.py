from django.shortcuts import render

from django.http import HttpResponse

from .forms import IndividualForm

# Create your views here.

def query(request):
	if request.method == 'POST':
		form = IndividualForm(request.POST)
		if form.is_valid():
			individual_id = form.cleaned_data['individual_id']
			
			return HttpResponse("This will be a query result for {:d}.".format(individual_id))
		else:
			return HttpResponse("Invalid form")
	else:
		form = IndividualForm()
		return render(request, 'samples/individuals.html', {'form': form})

def hello(request):
	return HttpResponse("Hello, world.")
