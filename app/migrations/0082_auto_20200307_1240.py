# Generated by Django 3.0.3 on 2020-03-07 04:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0081_auto_20200307_1010'),
    ]

    operations = [
        migrations.AlterField(
            model_name='clients',
            name='Device_Name',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='Device Name'),
        ),
    ]
