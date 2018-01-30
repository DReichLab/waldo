from django.urls import path, re_path

from . import views

urlpatterns = [
	path('updateRuns', views.updateSequencingRunList, name='Update sequencing runs'),
	path('start', views.startScreeningAnalysis, name='Start Analysis'),
	path('report_help', views.helpPage),
	re_path(r'^$', views.screeningForm, name='Screening analysis'),
]
