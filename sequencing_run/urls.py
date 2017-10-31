from django.conf.urls import url

from . import views

urlpatterns = [
	url(r'^updateRuns', views.updateSequencingRunList, name='Update sequencing runs'),
	url(r'^start', views.startScreeningAnalysis, name='Start Analysis'),
	url(r'^$', views.screeningForm, name='Screening analysis'),
]
