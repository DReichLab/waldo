from django.urls import path, re_path

from . import views

urlpatterns = [
	re_path(r'^query', views.query, name='query'),
	re_path(r'^library', views.library_id_to_instance, name='library'),
	re_path(r'^mt', views.mt_query, name='mt'),
	path('landing', views.landing, name='landing'),
	path('selection', views.sample_selection, name='selection'),
	path('well', views.well, name='well'),
	path('logout', views.logout_user, name='logout')
]
