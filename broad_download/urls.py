from django.urls import path, re_path

from . import views

urlpatterns = [
	re_path(r'^$', views.flowcell_download, name='Broad Institute Flowcell Downloads'),
]
 
