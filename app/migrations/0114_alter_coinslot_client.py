# Generated by Django 3.2.7 on 2021-10-03 21:07

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0113_clients_settings'),
    ]

    operations = [
        migrations.AlterField(
            model_name='coinslot',
            name='Client',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='app.clients'),
        ),
    ]
