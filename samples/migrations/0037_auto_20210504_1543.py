# Generated by Django 3.0.4 on 2021-05-04 19:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('samples', '0036_wetlabstaff_login_user'),
    ]

    operations = [
        migrations.AlterField(
            model_name='powderbatch',
            name='name',
            field=models.CharField(max_length=50, unique=True),
        ),
    ]