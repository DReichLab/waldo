from django.urls import path, re_path

from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth.views import PasswordChangeView

from . import views

urlpatterns = [
	re_path(r'^query', views.query, name='query'),
	#re_path(r'^library', views.library_id_to_instance, name='library'),
	re_path(r'^mt', views.mt_query, name='mt'),
	path('landing', views.landing, name='landing'),
	path('sample_prep_queue', views.sample_prep_queue, name='sample_prep_queue'),
	path('sample_prep_queue_view', views.sample_prep_queue_view, name='sample_prep_queue_view'),
	path('sample_prep_queue_spreadsheet', views.sample_prep_queue_spreadsheet, name='sample_prep_queue_spreadsheet'),
	
	path('powder_prep_queue_view', views.powder_prep_queue_view, name='powder_prep_queue_view'),
	path('powder_prep_queue_spreadsheet', views.powder_prep_queue_spreadsheet, name='powder_prep_queue_spreadsheet'),
	
	path('control_types', views.control_types, name='control_types'),
	path('control_sets', views.control_sets, name='control_sets'),
	path('control_set', views.control_set, name='control_set'),
	
	path('powder_batches', views.powder_batches, name='powder_batches'),
	path('powder_samples', views.powder_samples, name='powder_samples'), # powder samples in a powder batch
	path('powder_batch_assign_samples', views.powder_batch_assign_samples, name='powder_batch_assign_samples'),
	path('powder_batch_delete', views.powder_batch_delete, name='powder_batch_delete'),
	path('powder_samples_spreadsheet', views.powder_samples_spreadsheet, name='powder_samples_spreadsheet'),
	path('powder_samples_spreadsheet_upload', views.powder_samples_spreadsheet_upload, name='powder_samples_spreadsheet_upload'),
	
	path('extraction_protocols', views.extraction_protocols, name='extraction_protocols'),
	
	path('lysate_batch', views.lysate_batch, name='lysate_batch'),
	path('lysate_batch_assign_powder', views.lysate_batch_assign_powder, name='lysate_batch_assign_powder'),
	path('lysate_batch_delete', views.lysate_batch_delete, name='lysate_batch_delete'),
	path('lysate_batch_plate_layout', views.lysate_batch_plate_layout, name='lysate_batch_plate_layout'),
	path('lysates_in_batch', views.lysates_in_batch, name='lysates_in_batch'),
	path('lysates_spreadsheet', views.lysates_spreadsheet, name='lysates_spreadsheet'),
	path('lysates_spreadsheet_upload', views.lysates_spreadsheet_upload, name='lysates_spreadsheet_upload'),
	path('lysate_batch_to_extract_batch', views.lysate_batch_to_extract_batch, name='lysate_batch_to_extract_batch'),
	
	path('extract_batch', views.extract_batch, name='extract_batch'),
	path('extract_batch_assign_lysate', views.extract_batch_assign_lysate, name='extract_batch_assign_lysate'),
	path('extract_batch_add_lysate', views.extract_batch_add_lysate, name='extract_batch_add_lysate'),
	path('extract_batch_delete', views.extract_batch_delete, name='extract_batch_delete'),
	path('extract_batch_layout', views.extract_batch_layout, name='extract_batch_layout'),
	path('extracts_in_batch', views.extracts_in_batch, name='extracts_in_batch'),
	path('extracts_spreadsheet', views.extracts_spreadsheet, name='extracts_spreadsheet'),
	path('extracts_spreadsheet_upload', views.extracts_spreadsheet_upload, name='extracts_spreadsheet_upload'),
	path('extract_batch_load_crowd', views.extract_batch_load_crowd, name='extract_batch_load_crowd'),
	path('extract_batch_to_library_batch', views.extract_batch_to_library_batch, name='extract_batch_to_library_batch'),
	
	path('library_protocols', views.library_protocols, name='library_protocols'),
	path('library_protocol', views.library_protocol, name='library_protocol'),
	
	path('library_batches', views.library_batches, name='library_batches'),
	path('library_batch_assign_extract', views.library_batch_assign_extract, name='library_batch_assign_extract'),
	path('library_batch_delete', views.library_batch_delete, name='library_batch_delete'),
	path('library_batch_layout', views.library_batch_layout, name='library_batch_layout'),
	path('library_batch_barcodes_spreadsheet', views.library_batch_barcodes_spreadsheet, name='library_batch_barcodes_spreadsheet'),
	path('libraries_in_batch', views.libraries_in_batch, name='libraries_in_batch'),
	path('library_batch_to_capture_batch', views.library_batch_to_capture_batch, name='library_batch_to_capture_batch'),
	
	path('libraries_spreadsheet', views.libraries_spreadsheet, name='libraries_spreadsheet'),
	path('libraries_spreadsheet_upload', views.libraries_spreadsheet_upload, name='libraries_spreadsheet_upload'),
	
	path('capture_protocols', views.capture_protocols, name='capture_protocols'),
	path('capture_protocol', views.capture_protocol, name='capture_protocol'),
	
	path('capture_batches', views.capture_batches, name='capture_batches'),
	path('capture_batch_assign_library', views.capture_batch_assign_library, name='capture_batch_assign_library'),
	path('captures_in_batch', views.captures_in_batch, name='captures_in_batch'),
	path('capture_batch_layout', views.capture_batch_layout, name='capture_batch_layout'),
	path('capture_batch_spreadsheet', views.capture_batch_spreadsheet, name='capture_batch_spreadsheet'),
	path('capture_batch_delete', views.capture_batch_delete, name='capture_batch_delete'),
	path('capture_spreadsheet_upload', views.capture_spreadsheet_upload, name='capture_spreadsheet_upload'),
	path('capture_blob_spreadsheet_upload', views.capture_blob_spreadsheet_upload, name='capture_blob_spreadsheet_upload'),
	path('capture_batch_to_sequencing_run', views.capture_batch_to_sequencing_run, name='capture_batch_to_sequencing_run'),
	
	path('sequencing_runs', views.sequencing_runs, name='sequencing_runs'),
	path('sequencing_run_assign_captures', views.sequencing_run_assign_captures, name='sequencing_run_assign_captures'),
	path('sequencing_run_spreadsheet', views.sequencing_run_spreadsheet, name='sequencing_run_spreadsheet'),
	path('sequencing_run_delete', views.sequencing_run_delete, name='sequencing_run_delete'),
	
	path('sequencing_platforms', views.sequencing_platforms, name='sequencing_platforms'),
	path('sequencing_platform', views.sequencing_platform, name='sequencing_platform'),
	
	path('lost_powder', views.lost_powder, name='lost_powder'),
	path('lost_lysate', views.lost_lysate, name='lost_lysate'),
	path('sample', views.sample, name='sample'),
	path('delete_sample_photo', views.delete_sample_photo, name='delete_sample_photo'),
	path('sample_summary', views.sample_summary, name='sample_summary'),
	
	path('storage_all', views.storage_all, name='storage_all'),
	path('setup', views.setup, name='setup'),
	
	path('password_change', PasswordChangeView.as_view(success_url='password_changed'), name='password_change'),
	path('password_changed', views.password_changed, name='password_changed'),
	path('logout', views.logout_user, name='logout')
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
