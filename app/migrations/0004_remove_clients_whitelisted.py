# Generated by Django 4.0.4 on 2022-08-08 15:01

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0003_clients_whitelisted_alter_coinslot_last_updated'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='clients',
            name='Whitelisted',
        ),
    ]
