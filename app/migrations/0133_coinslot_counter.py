# Generated by Django 3.2.7 on 2021-11-11 05:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0132_alter_device_sync_time'),
    ]

    operations = [
        migrations.AddField(
            model_name='coinslot',
            name='Counter',
            field=models.IntegerField(default=0),
        ),
    ]
