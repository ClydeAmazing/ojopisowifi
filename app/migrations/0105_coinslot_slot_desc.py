# Generated by Django 3.0.8 on 2020-11-30 06:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0104_auto_20201130_1442'),
    ]

    operations = [
        migrations.AddField(
            model_name='coinslot',
            name='Slot_Desc',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
    ]
