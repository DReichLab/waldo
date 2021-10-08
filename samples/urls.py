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
	path('powder_samples_spreadsheet', views.powder_samples_spreadsheet, name='powder_samples_spreadsheet'),
	path('powder_samples_spreadsheet_upload', views.powder_samples_spreadsheet_upload, name='powder_samples_spreadsheet_upload'),
	path('extraction_protocols', views.extraction_protocols, name='extraction_protocols'),
	path('lysate_batch', views.lysate_batch, name='lysate_batch'),
	path('lysate_batch_assign_powder', views.lysate_batch_assign_powder, name='lysate_batch_assign_powder'),
	path('lysate_batch_plate_layout', views.lysate_batch_plate_layout, name='lysate_batch_plate_layout'),
	path('lysate_batch_to_extract_batch', views.lysate_batch_to_extract_batch, name='lysate_batch_to_extract_batch'),
	path('extract_batch', views.extract_batch, name='extract_batch'),
	path('extract_batch_assign_lysate', views.extract_batch_assign_lysate, name='extract_batch_assign_lysate'),
	path('extract_batch_add_lysate', views.extract_batch_add_lysate, name='extract_batch_add_lysate'),
	path('extract_batch_layout', views.extract_batch_layout, name='extract_batch_layout'),
	path('extract_batch_to_library_batch', views.extract_batch_to_library_batch, name='extract_batch_to_library_batch'),
	path('lost_powder', views.lost_powder, name='lost_powder'),
	path('lost_lysate', views.lost_lysate, name='lost_lysate'),
	path('sample', views.sample, name='sample'),
	
	path('password_change', PasswordChangeView.as_view(success_url='password_changed'), name='password_change'),
	path('password_changed', views.password_changed, name='password_changed'),
	path('logout', views.logout_user, name='logout')
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
