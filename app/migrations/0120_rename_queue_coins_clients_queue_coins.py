# Generated by Django 3.2.7 on 2021-10-16 17:12

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0119_clients_queue_coins'),
    ]

    operations = [
        migrations.RenameField(
            model_name='clients',
            old_name='queue_coins',
            new_name='Queue_Coins',
        ),
    ]
