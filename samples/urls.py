from django.urls import path, re_path

from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth.views import PasswordChangeView

from . import views

urlpatterns = [
	re_path(r'^query', views.query, name='query'),
	re_path(r'^library', views.library_id_to_instance, name='library'),
	re_path(r'^mt', views.mt_query, name='mt'),
	path('landing', views.landing, name='landing'),
	path('sample_prep_queue', views.sample_prep_queue, name='sample_prep_queue'),
	path('sample_prep_queue_view', views.sample_prep_queue_view, name='sample_prep_queue_view'),
	path('control_types', views.control_types, name='control_types'),
	path('control_layout', views.control_layout, name='control_layout'),
	path('powder_batches', views.powder_batches, name='powder_batches'),
	path('powder_samples', views.powder_samples, name='powder_samples'), # powder samples in a powder batch
	path('powder_batch_assign_samples', views.powder_batch_assign_samples, name='powder_batch_assign_samples'),
	path('extraction_protocols', views.extraction_protocols, name='extraction_protocols'),
	path('extract_batch', views.extract_batch, name='extract_batch'),
	path('extract_batch_assign_powder', views.extract_batch_assign_powder, name='extract_batch_assign_powder'),
	path('extract_batch_plate_layout', views.extract_batch_plate_layout, name='extract_batch_plate_layout'),
	path('sample', views.sample, name='sample'),
	path('well', views.well, name='well'),
	
	path('password_change', PasswordChangeView.as_view(success_url='password_changed'), name='password_change'),
	path('password_changed', views.password_changed, name='password_changed'),
	path('logout', views.logout_user, name='logout')
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
