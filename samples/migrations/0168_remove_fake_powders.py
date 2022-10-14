# Generated by Django 3.0.4 on 2022-08-10 18:40

from django.db import migrations

def remove_fake_powders(apps, lysate_batch):
	PowderSample = apps.get_model('samples', 'PowderSample')
	Lysate = apps.get_model('samples', 'Lysate')
	for powder_sample in PowderSample.objects.filter(powder_sample_id__endswith='.NP'):
		derived_lysates = Lysate.objects.filter(powder_sample=powder_sample)
		# Pride.24 needs to be excluded. This included Eadaoin's experiment with minimally invasive processing by dipping bone (tooth) into solution. There was no creation of powder, but lysate was generated from sample in the lab. 
		if derived_lysates.filter(lysate_batch__batch_name__startswith='Pride.24').count() == 0:
			for lysate in derived_lysates:
				lysate.powder_sample = None
				if lysate.sample and lysate.sample != powder_sample.sample:
					raise ValueError(f'sample mismatch for lysate {lysate.id}')
				lysate.sample = powder_sample.sample
				lysate.save()
			powder_sample.delete()

class Migration(migrations.Migration):

	dependencies = [
		('samples', '0167_remove_fake_lysates'),
	]

	operations = [
		migrations.RunPython(remove_fake_powders),
	]