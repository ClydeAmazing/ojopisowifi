# Generated by Django 3.2.7 on 2021-11-09 06:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0131_alter_coinslot_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='device',
            name='Sync_Time',
            field=models.DateTimeField(auto_now=True, null=True),
        ),
    ]
