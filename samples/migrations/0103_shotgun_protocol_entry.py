# Generated by Django 3.0.4 on 2021-11-11 17:46

from django.db import migrations

def create_shotgun_protocol_entry(apps, schema_editor):
	CaptureProtocol = apps.get_model('samples', 'CaptureProtocol')
	CaptureProtocol.objects.get_or_create(name='Raw', description='Shotgun, no capture')
	
def do_nothing(apps, schema_editor):
	pass

class Migration(migrations.Migration):

    dependencies = [
        ('samples', '0102_capture_names_are_not_unique'),
    ]

    operations = [
		migrations.RunPython(create_shotgun_protocol_entry, do_nothing),
    ]
