# Generated by Django 3.0.3 on 2023-03-30 18:13

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('samples', '0173_sequenced_library_many_to_many_through'),
    ]

    operations = [
        migrations.RenameField(
            model_name='sequencedlibrary',
            old_name='capturelayout',
            new_name='indexed_library',
        ),
        migrations.RenameField(
            model_name='sequencedlibrary',
            old_name='sequencingrun',
            new_name='sequencing_run',
        ),
        migrations.AddField(
            model_name='sequencedlibrary',
            name='created_by',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AddField(
            model_name='sequencedlibrary',
            name='creation_timestamp',
            field=models.DateTimeField(default=django.utils.timezone.now, null=True),
        ),
        migrations.AddField(
            model_name='sequencedlibrary',
            name='do_not_use',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='sequencedlibrary',
            name='modification_timestamp',
            field=models.DateTimeField(default=django.utils.timezone.now, null=True),
        ),
        migrations.AddField(
            model_name='sequencedlibrary',
            name='modified_by',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AddField(
            model_name='sequencedlibrary',
            name='notes',
            field=models.TextField(blank=True),
        ),
        migrations.AlterUniqueTogether(
            name='sequencedlibrary',
            unique_together={('indexed_library', 'sequencing_run')},
        ),
    ]
