# Generated by Django 3.0.4 on 2021-11-07 22:32

from django.db import migrations

def copy_protocol(queryset, apps):
	CaptureProtocol = apps.get_model('samples', 'CaptureProtocol')
	for x in queryset:
		protocol = x.protocol
		if protocol is None:
			x.protocol_temp = None
		else:
			x.protocol_temp = CaptureProtocol.objects.get(name=protocol.name)
		x.save()
		
def do_nothing(apps, schema_editor):
	pass

def copy_capture_protocols(apps, schema_editor):
	MTCapturePlate = apps.get_model('samples', 'MTCapturePlate')
	copy_protocol(MTCapturePlate.objects.all(), apps)
	NuclearCapturePlate = apps.get_model('samples', 'NuclearCapturePlate')
	copy_protocol(NuclearCapturePlate.objects.all(), apps)

class Migration(migrations.Migration):

    dependencies = [
        ('samples', '0098_references_to_single_capture_table'),
    ]

    operations = [
		migrations.RunPython(copy_capture_protocols, do_nothing),
    ]