# Generated by Django 3.2 on 2021-06-17 07:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('argus_notificationprofile', '0002_filter_filter'),
    ]

    operations = [
        migrations.AlterField(
            model_name='filter',
            name='filter',
            field=models.JSONField(default=dict),
        ),
    ]