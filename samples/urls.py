from django.urls import path, re_path

from . import views

urlpatterns = [
	re_path(r'^query', views.query, name='query'),
	re_path(r'^$', views.hello, name='Hello')
]
