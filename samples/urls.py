from django.urls import path, re_path

from django.contrib.auth.views import PasswordChangeView

from . import views

urlpatterns = [
	re_path(r'^query', views.query, name='query'),
	re_path(r'^library', views.library_id_to_instance, name='library'),
	re_path(r'^mt', views.mt_query, name='mt'),
	path('landing', views.landing, name='landing'),
	path('powder_batches', views.powder_batches, name='powder_batches'),
	path('powder_batch', views.powder_batch, name='powder_batch'),
	path('selection', views.sample_selection, name='selection'),
	path('well', views.well, name='well'),
	
	path('password_change', PasswordChangeView.as_view(success_url='password_changed'), name='password_change'),
	path('password_changed', views.password_changed, name='password_changed'),
	path('logout', views.logout_user, name='logout')
]
