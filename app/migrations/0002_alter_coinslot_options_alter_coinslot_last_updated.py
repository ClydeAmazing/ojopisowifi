# Generated by Django 4.0.4 on 2022-08-01 05:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='coinslot',
            options={'get_latest_by': 'Last_Updated', 'verbose_name': 'Coin Slot', 'verbose_name_plural': 'Coin Slot'},
        ),
        migrations.AlterField(
            model_name='coinslot',
            name='Last_Updated',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
