from django.urls import path, re_path

from . import views

urlpatterns = [
	re_path(r'^updateRuns', views.update_sequencing_run_list, name='Update sequencing runs'),
	re_path(r'^start', views.start_analysis_view, name='Start Analysis'),
	re_path(r'^report_help', views.help_page),
	re_path(r'^report_with_sample_sheet', views.report_with_sample_sheet_form),
	re_path(r'^$', views.analysis_form, name='Ancient DNA Analysis'),
]
