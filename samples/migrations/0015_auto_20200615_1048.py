# Generated by Django 3.0.4 on 2020-06-15 14:48

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('samples', '0014_auto_20200527_1236'),
    ]

    operations = [
        migrations.AlterField(
            model_name='collaborator',
            name='created_by',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AlterField(
            model_name='collaborator',
            name='creation_timestamp',
            field=models.DateTimeField(default=django.utils.timezone.now, null=True),
        ),
        migrations.AlterField(
            model_name='collaborator',
            name='modification_timestamp',
            field=models.DateTimeField(default=django.utils.timezone.now, null=True),
        ),
        migrations.AlterField(
            model_name='collaborator',
            name='modified_by',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AlterField(
            model_name='controlsextract',
            name='created_by',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AlterField(
            model_name='controlsextract',
            name='creation_timestamp',
            field=models.DateTimeField(default=django.utils.timezone.now, null=True),
        ),
        migrations.AlterField(
            model_name='controlsextract',
            name='modification_timestamp',
            field=models.DateTimeField(default=django.utils.timezone.now, null=True),
        ),
        migrations.AlterField(
            model_name='controlsextract',
            name='modified_by',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AlterField(
            model_name='controlslibrary',
            name='created_by',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AlterField(
            model_name='controlslibrary',
            name='creation_timestamp',
            field=models.DateTimeField(default=django.utils.timezone.now, null=True),
        ),
        migrations.AlterField(
            model_name='controlslibrary',
            name='modification_timestamp',
            field=models.DateTimeField(default=django.utils.timezone.now, null=True),
        ),
        migrations.AlterField(
            model_name='controlslibrary',
            name='modified_by',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AlterField(
            model_name='distributionsextract',
            name='created_by',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AlterField(
            model_name='distributionsextract',
            name='creation_timestamp',
            field=models.DateTimeField(default=django.utils.timezone.now, null=True),
        ),
        migrations.AlterField(
            model_name='distributionsextract',
            name='modification_timestamp',
            field=models.DateTimeField(default=django.utils.timezone.now, null=True),
        ),
        migrations.AlterField(
            model_name='distributionsextract',
            name='modified_by',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AlterField(
            model_name='distributionslysate',
            name='created_by',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AlterField(
            model_name='distributionslysate',
            name='creation_timestamp',
            field=models.DateTimeField(default=django.utils.timezone.now, null=True),
        ),
        migrations.AlterField(
            model_name='distributionslysate',
            name='modification_timestamp',
            field=models.DateTimeField(default=django.utils.timezone.now, null=True),
        ),
        migrations.AlterField(
            model_name='distributionslysate',
            name='modified_by',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AlterField(
            model_name='distributionspowder',
            name='created_by',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AlterField(
            model_name='distributionspowder',
            name='creation_timestamp',
            field=models.DateTimeField(default=django.utils.timezone.now, null=True),
        ),
        migrations.AlterField(
            model_name='distributionspowder',
            name='modification_timestamp',
            field=models.DateTimeField(default=django.utils.timezone.now, null=True),
        ),
        migrations.AlterField(
            model_name='distributionspowder',
            name='modified_by',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AlterField(
            model_name='distributionsshipment',
            name='created_by',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AlterField(
            model_name='distributionsshipment',
            name='creation_timestamp',
            field=models.DateTimeField(default=django.utils.timezone.now, null=True),
        ),
        migrations.AlterField(
            model_name='distributionsshipment',
            name='modification_timestamp',
            field=models.DateTimeField(default=django.utils.timezone.now, null=True),
        ),
        migrations.AlterField(
            model_name='distributionsshipment',
            name='modified_by',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AlterField(
            model_name='extract',
            name='created_by',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AlterField(
            model_name='extract',
            name='creation_timestamp',
            field=models.DateTimeField(default=django.utils.timezone.now, null=True),
        ),
        migrations.AlterField(
            model_name='extract',
            name='modification_timestamp',
            field=models.DateTimeField(default=django.utils.timezone.now, null=True),
        ),
        migrations.AlterField(
            model_name='extract',
            name='modified_by',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AlterField(
            model_name='extractbatch',
            name='created_by',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AlterField(
            model_name='extractbatch',
            name='creation_timestamp',
            field=models.DateTimeField(default=django.utils.timezone.now, null=True),
        ),
        migrations.AlterField(
            model_name='extractbatch',
            name='modification_timestamp',
            field=models.DateTimeField(default=django.utils.timezone.now, null=True),
        ),
        migrations.AlterField(
            model_name='extractbatch',
            name='modified_by',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AlterField(
            model_name='extractionprotocol',
            name='created_by',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AlterField(
            model_name='extractionprotocol',
            name='creation_timestamp',
            field=models.DateTimeField(default=django.utils.timezone.now, null=True),
        ),
        migrations.AlterField(
            model_name='extractionprotocol',
            name='modification_timestamp',
            field=models.DateTimeField(default=django.utils.timezone.now, null=True),
        ),
        migrations.AlterField(
            model_name='extractionprotocol',
            name='modified_by',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AlterField(
            model_name='instance',
            name='created_by',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AlterField(
            model_name='instance',
            name='creation_timestamp',
            field=models.DateTimeField(default=django.utils.timezone.now, null=True),
        ),
        migrations.AlterField(
            model_name='instance',
            name='modification_timestamp',
            field=models.DateTimeField(default=django.utils.timezone.now, null=True),
        ),
        migrations.AlterField(
            model_name='instance',
            name='modified_by',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AlterField(
            model_name='library',
            name='created_by',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AlterField(
            model_name='library',
            name='creation_timestamp',
            field=models.DateTimeField(default=django.utils.timezone.now, null=True),
        ),
        migrations.AlterField(
            model_name='library',
            name='modification_timestamp',
            field=models.DateTimeField(default=django.utils.timezone.now, null=True),
        ),
        migrations.AlterField(
            model_name='library',
            name='modified_by',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AlterField(
            model_name='librarybatch',
            name='created_by',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AlterField(
            model_name='librarybatch',
            name='creation_timestamp',
            field=models.DateTimeField(default=django.utils.timezone.now, null=True),
        ),
        migrations.AlterField(
            model_name='librarybatch',
            name='modification_timestamp',
            field=models.DateTimeField(default=django.utils.timezone.now, null=True),
        ),
        migrations.AlterField(
            model_name='librarybatch',
            name='modified_by',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AlterField(
            model_name='libraryprotocol',
            name='created_by',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AlterField(
            model_name='libraryprotocol',
            name='creation_timestamp',
            field=models.DateTimeField(default=django.utils.timezone.now, null=True),
        ),
        migrations.AlterField(
            model_name='libraryprotocol',
            name='modification_timestamp',
            field=models.DateTimeField(default=django.utils.timezone.now, null=True),
        ),
        migrations.AlterField(
            model_name='libraryprotocol',
            name='modified_by',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AlterField(
            model_name='lysate',
            name='created_by',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AlterField(
            model_name='lysate',
            name='creation_timestamp',
            field=models.DateTimeField(default=django.utils.timezone.now, null=True),
        ),
        migrations.AlterField(
            model_name='lysate',
            name='modification_timestamp',
            field=models.DateTimeField(default=django.utils.timezone.now, null=True),
        ),
        migrations.AlterField(
            model_name='lysate',
            name='modified_by',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AlterField(
            model_name='mtcaptureplate',
            name='created_by',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AlterField(
            model_name='mtcaptureplate',
            name='creation_timestamp',
            field=models.DateTimeField(default=django.utils.timezone.now, null=True),
        ),
        migrations.AlterField(
            model_name='mtcaptureplate',
            name='modification_timestamp',
            field=models.DateTimeField(default=django.utils.timezone.now, null=True),
        ),
        migrations.AlterField(
            model_name='mtcaptureplate',
            name='modified_by',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AlterField(
            model_name='mtcaptureprotocol',
            name='created_by',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AlterField(
            model_name='mtcaptureprotocol',
            name='creation_timestamp',
            field=models.DateTimeField(default=django.utils.timezone.now, null=True),
        ),
        migrations.AlterField(
            model_name='mtcaptureprotocol',
            name='modification_timestamp',
            field=models.DateTimeField(default=django.utils.timezone.now, null=True),
        ),
        migrations.AlterField(
            model_name='mtcaptureprotocol',
            name='modified_by',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AlterField(
            model_name='mtsequencingrun',
            name='created_by',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AlterField(
            model_name='mtsequencingrun',
            name='creation_timestamp',
            field=models.DateTimeField(default=django.utils.timezone.now, null=True),
        ),
        migrations.AlterField(
            model_name='mtsequencingrun',
            name='modification_timestamp',
            field=models.DateTimeField(default=django.utils.timezone.now, null=True),
        ),
        migrations.AlterField(
            model_name='mtsequencingrun',
            name='modified_by',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AlterField(
            model_name='nuclearcaptureplate',
            name='created_by',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AlterField(
            model_name='nuclearcaptureplate',
            name='creation_timestamp',
            field=models.DateTimeField(default=django.utils.timezone.now, null=True),
        ),
        migrations.AlterField(
            model_name='nuclearcaptureplate',
            name='modification_timestamp',
            field=models.DateTimeField(default=django.utils.timezone.now, null=True),
        ),
        migrations.AlterField(
            model_name='nuclearcaptureplate',
            name='modified_by',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AlterField(
            model_name='nuclearcaptureprotocol',
            name='created_by',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AlterField(
            model_name='nuclearcaptureprotocol',
            name='creation_timestamp',
            field=models.DateTimeField(default=django.utils.timezone.now, null=True),
        ),
        migrations.AlterField(
            model_name='nuclearcaptureprotocol',
            name='modification_timestamp',
            field=models.DateTimeField(default=django.utils.timezone.now, null=True),
        ),
        migrations.AlterField(
            model_name='nuclearcaptureprotocol',
            name='modified_by',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AlterField(
            model_name='nuclearsequencingrun',
            name='created_by',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AlterField(
            model_name='nuclearsequencingrun',
            name='creation_timestamp',
            field=models.DateTimeField(default=django.utils.timezone.now, null=True),
        ),
        migrations.AlterField(
            model_name='nuclearsequencingrun',
            name='modification_timestamp',
            field=models.DateTimeField(default=django.utils.timezone.now, null=True),
        ),
        migrations.AlterField(
            model_name='nuclearsequencingrun',
            name='modified_by',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AlterField(
            model_name='powderbatch',
            name='created_by',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AlterField(
            model_name='powderbatch',
            name='creation_timestamp',
            field=models.DateTimeField(default=django.utils.timezone.now, null=True),
        ),
        migrations.AlterField(
            model_name='powderbatch',
            name='modification_timestamp',
            field=models.DateTimeField(default=django.utils.timezone.now, null=True),
        ),
        migrations.AlterField(
            model_name='powderbatch',
            name='modified_by',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AlterField(
            model_name='powdersample',
            name='created_by',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AlterField(
            model_name='powdersample',
            name='creation_timestamp',
            field=models.DateTimeField(default=django.utils.timezone.now, null=True),
        ),
        migrations.AlterField(
            model_name='powdersample',
            name='modification_timestamp',
            field=models.DateTimeField(default=django.utils.timezone.now, null=True),
        ),
        migrations.AlterField(
            model_name='powdersample',
            name='modified_by',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AlterField(
            model_name='publication',
            name='created_by',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AlterField(
            model_name='publication',
            name='creation_timestamp',
            field=models.DateTimeField(default=django.utils.timezone.now, null=True),
        ),
        migrations.AlterField(
            model_name='publication',
            name='modification_timestamp',
            field=models.DateTimeField(default=django.utils.timezone.now, null=True),
        ),
        migrations.AlterField(
            model_name='publication',
            name='modified_by',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AlterField(
            model_name='radiocarbondatedsample',
            name='created_by',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AlterField(
            model_name='radiocarbondatedsample',
            name='creation_timestamp',
            field=models.DateTimeField(default=django.utils.timezone.now, null=True),
        ),
        migrations.AlterField(
            model_name='radiocarbondatedsample',
            name='modification_timestamp',
            field=models.DateTimeField(default=django.utils.timezone.now, null=True),
        ),
        migrations.AlterField(
            model_name='radiocarbondatedsample',
            name='modified_by',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AlterField(
            model_name='radiocarbondatinginvoice',
            name='created_by',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AlterField(
            model_name='radiocarbondatinginvoice',
            name='creation_timestamp',
            field=models.DateTimeField(default=django.utils.timezone.now, null=True),
        ),
        migrations.AlterField(
            model_name='radiocarbondatinginvoice',
            name='modification_timestamp',
            field=models.DateTimeField(default=django.utils.timezone.now, null=True),
        ),
        migrations.AlterField(
            model_name='radiocarbondatinginvoice',
            name='modified_by',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AlterField(
            model_name='radiocarbonshipment',
            name='created_by',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AlterField(
            model_name='radiocarbonshipment',
            name='creation_timestamp',
            field=models.DateTimeField(default=django.utils.timezone.now, null=True),
        ),
        migrations.AlterField(
            model_name='radiocarbonshipment',
            name='modification_timestamp',
            field=models.DateTimeField(default=django.utils.timezone.now, null=True),
        ),
        migrations.AlterField(
            model_name='radiocarbonshipment',
            name='modified_by',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AlterField(
            model_name='results',
            name='created_by',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AlterField(
            model_name='results',
            name='creation_timestamp',
            field=models.DateTimeField(default=django.utils.timezone.now, null=True),
        ),
        migrations.AlterField(
            model_name='results',
            name='modification_timestamp',
            field=models.DateTimeField(default=django.utils.timezone.now, null=True),
        ),
        migrations.AlterField(
            model_name='results',
            name='modified_by',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AlterField(
            model_name='return',
            name='created_by',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AlterField(
            model_name='return',
            name='creation_timestamp',
            field=models.DateTimeField(default=django.utils.timezone.now, null=True),
        ),
        migrations.AlterField(
            model_name='return',
            name='modification_timestamp',
            field=models.DateTimeField(default=django.utils.timezone.now, null=True),
        ),
        migrations.AlterField(
            model_name='return',
            name='modified_by',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AlterField(
            model_name='sample',
            name='created_by',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AlterField(
            model_name='sample',
            name='creation_timestamp',
            field=models.DateTimeField(default=django.utils.timezone.now, null=True),
        ),
        migrations.AlterField(
            model_name='sample',
            name='modification_timestamp',
            field=models.DateTimeField(default=django.utils.timezone.now, null=True),
        ),
        migrations.AlterField(
            model_name='sample',
            name='modified_by',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AlterField(
            model_name='sampleprepprotocol',
            name='created_by',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AlterField(
            model_name='sampleprepprotocol',
            name='creation_timestamp',
            field=models.DateTimeField(default=django.utils.timezone.now, null=True),
        ),
        migrations.AlterField(
            model_name='sampleprepprotocol',
            name='modification_timestamp',
            field=models.DateTimeField(default=django.utils.timezone.now, null=True),
        ),
        migrations.AlterField(
            model_name='sampleprepprotocol',
            name='modified_by',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AlterField(
            model_name='sequencingplatform',
            name='created_by',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AlterField(
            model_name='sequencingplatform',
            name='creation_timestamp',
            field=models.DateTimeField(default=django.utils.timezone.now, null=True),
        ),
        migrations.AlterField(
            model_name='sequencingplatform',
            name='modification_timestamp',
            field=models.DateTimeField(default=django.utils.timezone.now, null=True),
        ),
        migrations.AlterField(
            model_name='sequencingplatform',
            name='modified_by',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AlterField(
            model_name='shipment',
            name='created_by',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AlterField(
            model_name='shipment',
            name='creation_timestamp',
            field=models.DateTimeField(default=django.utils.timezone.now, null=True),
        ),
        migrations.AlterField(
            model_name='shipment',
            name='modification_timestamp',
            field=models.DateTimeField(default=django.utils.timezone.now, null=True),
        ),
        migrations.AlterField(
            model_name='shipment',
            name='modified_by',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AlterField(
            model_name='shotgunpool',
            name='created_by',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AlterField(
            model_name='shotgunpool',
            name='creation_timestamp',
            field=models.DateTimeField(default=django.utils.timezone.now, null=True),
        ),
        migrations.AlterField(
            model_name='shotgunpool',
            name='modification_timestamp',
            field=models.DateTimeField(default=django.utils.timezone.now, null=True),
        ),
        migrations.AlterField(
            model_name='shotgunpool',
            name='modified_by',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AlterField(
            model_name='shotgunsequencingrun',
            name='created_by',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AlterField(
            model_name='shotgunsequencingrun',
            name='creation_timestamp',
            field=models.DateTimeField(default=django.utils.timezone.now, null=True),
        ),
        migrations.AlterField(
            model_name='shotgunsequencingrun',
            name='modification_timestamp',
            field=models.DateTimeField(default=django.utils.timezone.now, null=True),
        ),
        migrations.AlterField(
            model_name='shotgunsequencingrun',
            name='modified_by',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AlterField(
            model_name='supportstaff',
            name='created_by',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AlterField(
            model_name='supportstaff',
            name='creation_timestamp',
            field=models.DateTimeField(default=django.utils.timezone.now, null=True),
        ),
        migrations.AlterField(
            model_name='supportstaff',
            name='modification_timestamp',
            field=models.DateTimeField(default=django.utils.timezone.now, null=True),
        ),
        migrations.AlterField(
            model_name='supportstaff',
            name='modified_by',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AlterField(
            model_name='wetlabstaff',
            name='created_by',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AlterField(
            model_name='wetlabstaff',
            name='creation_timestamp',
            field=models.DateTimeField(default=django.utils.timezone.now, null=True),
        ),
        migrations.AlterField(
            model_name='wetlabstaff',
            name='modification_timestamp',
            field=models.DateTimeField(default=django.utils.timezone.now, null=True),
        ),
        migrations.AlterField(
            model_name='wetlabstaff',
            name='modified_by',
            field=models.CharField(blank=True, max_length=20),
        ),
    ]