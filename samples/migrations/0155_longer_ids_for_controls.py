# Generated by Django 3.0.4 on 2022-06-15 19:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('samples', '0154_auto_20220608_1442'),
    ]

    operations = [
        migrations.AlterField(
            model_name='extract',
            name='extract_id',
            field=models.CharField(db_index=True, max_length=50, unique=True),
        ),
        migrations.AlterField(
            model_name='library',
            name='reich_lab_library_id',
            field=models.CharField(db_index=True, max_length=50, unique=True),
        ),
        migrations.AlterField(
            model_name='lysate',
            name='lysate_id',
            field=models.CharField(db_index=True, max_length=50, unique=True),
        ),
    ]