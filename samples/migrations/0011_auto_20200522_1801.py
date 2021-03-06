# Generated by Django 3.0.4 on 2020-05-22 22:01

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('samples', '0010_auto_20200521_1453'),
    ]

    operations = [
        migrations.CreateModel(
            name='SamplePrepProtocol',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('creation_timestamp', models.DateTimeField(default=django.utils.timezone.now)),
                ('created_by', models.CharField(max_length=20)),
                ('modification_timestamp', models.DateTimeField(default=django.utils.timezone.now)),
                ('modified_by', models.CharField(max_length=20)),
                ('preparation_method', models.CharField(help_text='Method used to produce bone powder', max_length=50)),
                ('manuscript_summary', models.TextField(help_text='Sampling method summary for manuscripts')),
                ('protocol_reference', models.TextField(blank=True, help_text='Protocol citation')),
                ('notes', models.TextField(blank=True, help_text='Notes about the method used to create bone powder')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='SequencingPlatform',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('creation_timestamp', models.DateTimeField(default=django.utils.timezone.now)),
                ('created_by', models.CharField(max_length=20)),
                ('modification_timestamp', models.DateTimeField(default=django.utils.timezone.now)),
                ('modified_by', models.CharField(max_length=20)),
                ('platform', models.CharField(max_length=20)),
                ('library_type', models.CharField(blank=True, max_length=20)),
                ('read_length', models.CharField(max_length=20)),
                ('note', models.TextField()),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='SupportStaff',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('creation_timestamp', models.DateTimeField(default=django.utils.timezone.now)),
                ('created_by', models.CharField(max_length=20)),
                ('modification_timestamp', models.DateTimeField(default=django.utils.timezone.now)),
                ('modified_by', models.CharField(max_length=20)),
                ('first_name', models.CharField(db_index=True, max_length=30)),
                ('late_name', models.CharField(db_index=True, max_length=30)),
                ('start_date', models.DateField(null=True)),
                ('end_date', models.DateField(null=True)),
                ('title', models.CharField(max_length=50)),
                ('email_1', models.CharField(blank=True, max_length=50)),
                ('email_2', models.CharField(blank=True, max_length=50)),
                ('phone_number', models.CharField(blank=True, max_length=30)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='WetLabStaff',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('creation_timestamp', models.DateTimeField(default=django.utils.timezone.now)),
                ('created_by', models.CharField(max_length=20)),
                ('modification_timestamp', models.DateTimeField(default=django.utils.timezone.now)),
                ('modified_by', models.CharField(max_length=20)),
                ('first_name', models.CharField(db_index=True, max_length=30)),
                ('late_name', models.CharField(db_index=True, max_length=30)),
                ('start_date', models.DateField(null=True)),
                ('end_date', models.DateField(null=True)),
                ('title', models.CharField(max_length=50)),
                ('email_1', models.CharField(blank=True, max_length=50)),
                ('email_2', models.CharField(blank=True, max_length=50)),
                ('phone_number', models.CharField(blank=True, max_length=30)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.RenameField(
            model_name='extractionprotocol',
            old_name='update_description',
            new_name='description',
        ),
        migrations.RenameField(
            model_name='extractionprotocol',
            old_name='publication_summary',
            new_name='protocol_reference',
        ),
        migrations.RenameField(
            model_name='libraryprotocol',
            old_name='update_description',
            new_name='description',
        ),
        migrations.RenameField(
            model_name='libraryprotocol',
            old_name='publication_summary',
            new_name='protocol_reference',
        ),
        migrations.RenameField(
            model_name='mtcaptureprotocol',
            old_name='update_description',
            new_name='description',
        ),
        migrations.RenameField(
            model_name='nuclearcaptureprotocol',
            old_name='update_description',
            new_name='description',
        ),
        migrations.RenameField(
            model_name='nuclearcaptureprotocol',
            old_name='publication_summary',
            new_name='protocol_reference',
        ),
        migrations.RenameField(
            model_name='shipment',
            old_name='text_id',
            new_name='shipment_name',
        ),
        migrations.AddField(
            model_name='extract',
            name='extraction_lab',
            field=models.CharField(blank=True, help_text='Name of lab where DNA extraction was done', max_length=50),
        ),
        migrations.AddField(
            model_name='library',
            name='library_prep_lab',
            field=models.CharField(blank=True, help_text='Name of lab where library preparation was done', max_length=50),
        ),
        migrations.AddField(
            model_name='mtcaptureprotocol',
            name='manuscript_summary',
            field=models.TextField(blank=True, help_text='Enrichment method summary for manuscripts'),
        ),
        migrations.AddField(
            model_name='nuclearcaptureprotocol',
            name='manuscript_summary',
            field=models.TextField(blank=True, help_text='Enrichment method summary for manuscripts'),
        ),
        migrations.AddField(
            model_name='powdersample',
            name='sample_prep_lab',
            field=models.CharField(blank=True, help_text='Name of lab where bone powder was produced', max_length=50),
        ),
        migrations.AddField(
            model_name='sample',
            name='culture',
            field=models.CharField(blank=True, help_text='Archaeologic culture component of group label of an Individual', max_length=50),
        ),
        migrations.AddField(
            model_name='sample',
            name='geo_region',
            field=models.CharField(blank=True, help_text='Geographic region component of group label of an Individual', max_length=50),
        ),
        migrations.AddField(
            model_name='sample',
            name='geo_subregion',
            field=models.CharField(blank=True, help_text='Geographic subregion component of group label of an Individual', max_length=50),
        ),
        migrations.AddField(
            model_name='sample',
            name='outlier',
            field=models.CharField(blank=True, help_text='Outlier designation component of group label of an Individual', max_length=50),
        ),
        migrations.AddField(
            model_name='sample',
            name='period',
            field=models.CharField(blank=True, help_text='Archaeologic period component of group label of an Individual', max_length=50),
        ),
        migrations.AlterField(
            model_name='collaborator',
            name='first_name',
            field=models.CharField(db_index=True, max_length=50),
        ),
        migrations.AlterField(
            model_name='collaborator',
            name='last_name',
            field=models.CharField(db_index=True, max_length=50),
        ),
        migrations.AlterField(
            model_name='extractionprotocol',
            name='reference_abbreviation',
            field=models.CharField(blank=True, max_length=150),
        ),
        migrations.AlterField(
            model_name='libraryprotocol',
            name='library_method_reference_abbreviation',
            field=models.CharField(blank=True, max_length=50),
        ),
        migrations.AlterField(
            model_name='mtcaptureprotocol',
            name='publication_summary',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='extractbatch',
            name='technician_fk',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='samples.WetLabStaff'),
        ),
        migrations.AddField(
            model_name='librarybatch',
            name='technician_fk',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='samples.WetLabStaff'),
        ),
        migrations.AddField(
            model_name='mtcaptureplate',
            name='technician_fk',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='samples.WetLabStaff'),
        ),
        migrations.AddField(
            model_name='mtsequencingrun',
            name='sequencing',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='samples.SequencingPlatform'),
        ),
        migrations.AddField(
            model_name='mtsequencingrun',
            name='technician_fk',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='samples.WetLabStaff'),
        ),
        migrations.AddField(
            model_name='nuclearcaptureplate',
            name='technician_fk',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='samples.WetLabStaff'),
        ),
        migrations.AddField(
            model_name='nuclearsequencingrun',
            name='sequencing',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='samples.SequencingPlatform'),
        ),
        migrations.AddField(
            model_name='nuclearsequencingrun',
            name='technician_fk',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='samples.WetLabStaff'),
        ),
        migrations.AddField(
            model_name='powderbatch',
            name='technician_fk',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='samples.WetLabStaff'),
        ),
        migrations.AddField(
            model_name='powdersample',
            name='sample_prep_protocol',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='samples.SamplePrepProtocol'),
        ),
        migrations.AddField(
            model_name='shotgunpool',
            name='technician_fk',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='samples.WetLabStaff'),
        ),
        migrations.AddField(
            model_name='shotgunsequencingrun',
            name='sequencing',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='samples.SequencingPlatform'),
        ),
        migrations.AddField(
            model_name='shotgunsequencingrun',
            name='technician_fk',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='samples.WetLabStaff'),
        ),
    ]
