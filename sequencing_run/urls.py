from django.urls import path, re_path

from . import views

urlpatterns = [
	re_path(r'^updateRuns', views.updateSequencingRunList, name='Update sequencing runs'),
	re_path(r'^start', views.startScreeningAnalysis, name='Start Analysis'),
	re_path(r'^report_help', views.helpPage),
	re_path(r'^$', views.screeningForm, name='Screening analysis'),
]
