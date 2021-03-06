# Generated by Django 3.0.4 on 2021-10-19 17:13

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('samples', '0073_library_batch_cleanup_and_qpcr'),
    ]

    operations = [
        migrations.AddField(
            model_name='lysatebatchlayout',
            name='lysate',
            field=models.ForeignKey(help_text='Lysate created in this well from powder', null=True, on_delete=django.db.models.deletion.SET_NULL, to='samples.Lysate'),
        ),
    ]
