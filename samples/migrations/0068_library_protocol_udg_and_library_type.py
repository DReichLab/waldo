# Generated by Django 3.0.4 on 2021-10-14 17:03

from django.db import migrations, models

# read out UDG treatment and strandedness from the text label
def copy_udg_strandedmess(apps, schema_editor):
	LibraryProtocol = apps.get_model('samples', 'LibraryProtocol')
	for protocol in LibraryProtocol.objects.all():
		if 'ds' in protocol.name:
			protocol.library_type = 'ds'
		elif 'ss' in protocol.name:
			protocol.library_type = 'ss'
		else:
			print(f'no library type assigned for protocol {protocol.name}')
		
		if 'UDGpartial' in protocol.name:
			protocol.udg_treatment = 'partial'
		elif 'UDGminus' in protocol.name:
			protocol.udg_treatment = 'minus'
		elif 'UDG+' in protocol.name:
			protocol.udg_treatment = 'plus'
		else:
			print(f'no udg treatment assigned for protocol {protocol.name}')
		protocol.save()
		
# text label was unchanged, so we need not do anything to reverse
def do_nothing(apps, schema_editor):
	pass

class Migration(migrations.Migration):

    dependencies = [
        ('samples', '0067_auto_20211012_1700'),
    ]

    operations = [
        migrations.AddField(
            model_name='libraryprotocol',
            name='library_type',
            field=models.CharField(max_length=2, null=True),
        ),
        migrations.AddField(
            model_name='libraryprotocol',
            name='udg_treatment',
            field=models.CharField(max_length=10, null=True),
        ),
		migrations.RunPython(copy_udg_strandedmess, do_nothing),
    ]
