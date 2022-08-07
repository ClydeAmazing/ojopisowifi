# Generated by Django 4.0.4 on 2022-07-30 11:10

import datetime
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Clients',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('IP_Address', models.CharField(max_length=15, verbose_name='IP')),
                ('MAC_Address', models.CharField(max_length=255, unique=True, verbose_name='MAC Address')),
                ('Device_Name', models.CharField(blank=True, max_length=255, null=True, verbose_name='Device Name')),
                ('Time_Left', models.DurationField(default=datetime.timedelta(0))),
                ('Connected_On', models.DateTimeField(blank=True, null=True)),
                ('Expire_On', models.DateTimeField(blank=True, null=True)),
                ('Upload_Rate', models.IntegerField(default=0, help_text='Specify client internet upload bandwidth in Kbps. No value = unlimited bandwidth', verbose_name='Upload Bandwidth')),
                ('Download_Rate', models.IntegerField(default=0, help_text='Specify client internet download bandwidth in Kbps. No value = unlimited bandwidth', verbose_name='Download Bandwidth')),
                ('Notification_ID', models.CharField(blank=True, max_length=255, null=True, verbose_name='Notification ID')),
                ('Notified_Flag', models.BooleanField(default=False)),
                ('Date_Created', models.DateTimeField(auto_now_add=True)),
                ('FAS_Session', models.CharField(max_length=500, unique=True)),
            ],
            options={
                'verbose_name': 'Client',
                'verbose_name_plural': 'Clients',
            },
        ),
        migrations.CreateModel(
            name='Device',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('Device_ID', models.CharField(blank=True, max_length=255, null=True)),
                ('Ethernet_MAC', models.CharField(blank=True, max_length=50, null=True)),
                ('Device_SN', models.CharField(blank=True, max_length=50, null=True)),
                ('pub_rsa', models.TextField()),
                ('ca', models.CharField(max_length=200, unique=True)),
                ('action', models.IntegerField(default=0)),
                ('Sync_Time', models.DateTimeField(auto_now=True, null=True)),
            ],
            options={
                'verbose_name': 'Hardware',
            },
        ),
        migrations.CreateModel(
            name='Ledger',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('Date', models.DateTimeField(auto_now_add=True, verbose_name='Transaction Date')),
                ('Client', models.CharField(max_length=50)),
                ('Denomination', models.IntegerField()),
                ('Slot_No', models.IntegerField()),
            ],
            options={
                'verbose_name': 'Ledger',
                'verbose_name_plural': 'Ledger',
            },
        ),
        migrations.CreateModel(
            name='Network',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('Server_IP', models.GenericIPAddressField(default='10.0.0.1', protocol='IPv4', verbose_name='Server IP')),
                ('Netmask', models.GenericIPAddressField(default='255.255.255.0', protocol='IPv4')),
                ('DNS_1', models.GenericIPAddressField(default='8.8.8.8', protocol='IPv4', verbose_name='DNS 1')),
                ('DNS_2', models.GenericIPAddressField(blank=True, default='8.8.4.4', null=True, protocol='IPv4', verbose_name='DNS 2 (Optional)')),
                ('Upload_Rate', models.IntegerField(default=0, help_text='Specify global internet upload bandwidth in Kbps. 0 = unlimited bandwidth', verbose_name='Upload Limit')),
                ('Download_Rate', models.IntegerField(default=0, help_text='Specify global internet download bandwidth in Kbps. 0 = unlimited bandwidth', verbose_name='Download Limit')),
                ('Limit_Allowed_Clients', models.BooleanField(default=False, help_text='Check if bandwith limiting should also be applied to Allowed/Whitelisted devices.')),
            ],
            options={
                'verbose_name': 'Networking',
            },
        ),
        migrations.CreateModel(
            name='PushNotifications',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('Enabled', models.BooleanField(default=False)),
                ('app_id', models.CharField(blank=True, max_length=255, null=True, verbose_name='OneSignal App ID')),
                ('api_key', models.CharField(blank=True, max_length=255, null=True, verbose_name='OneSignal API Key')),
                ('notification_title', models.CharField(blank=True, max_length=255, null=True, verbose_name='Notification Title')),
                ('notification_message', models.CharField(blank=True, max_length=255, null=True, verbose_name='Notification Message')),
                ('notification_trigger_time', models.DurationField(blank=True, default=datetime.timedelta(0), help_text='Notification will fire when time is equal to the specified trigger time. Format: hh:mm:ss', null=True, verbose_name='Notification Trigger')),
            ],
            options={
                'verbose_name': 'Push Notifications',
            },
        ),
        migrations.CreateModel(
            name='Rates',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('Denom', models.IntegerField(help_text='Coin denomination corresponding to specified coinslot pulse.', verbose_name='Denomination')),
                ('Pulse', models.IntegerField(blank=True, help_text='Coinslot pulse count corresponding to coin denomination. Leave it blank for promotional rates.', null=True)),
                ('Minutes', models.DurationField(default=datetime.timedelta(0), help_text='Internet access duration in hh:mm:ss format', verbose_name='Duration (Custom)')),
            ],
            options={
                'verbose_name': 'Rate',
                'verbose_name_plural': 'Rates',
            },
        ),
        migrations.CreateModel(
            name='Settings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('Hotspot_Name', models.CharField(max_length=255)),
                ('Hotspot_Address', models.CharField(blank=True, max_length=255, null=True)),
                ('Slot_Timeout', models.PositiveIntegerField(default=15, help_text='Slot timeout in seconds. Default is 15', validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(30)])),
                ('Rate_Type', models.CharField(choices=[('auto', 'Minutes/Peso'), ('manual', 'Custom Rate')], default='auto', help_text='Select "Minutes/Peso" to use  Minutes / Peso value, else use "Custom Rate" to manually setup Rates based on coin value.', max_length=25)),
                ('Base_Value', models.DurationField(default=datetime.timedelta(0), help_text='Base time value for each peso. Specify in hh:mm:ss format. Applicable only if Rate Type is Minutes/Peso', verbose_name='Minutes / Peso')),
                ('Inactive_Timeout', models.IntegerField(help_text='Timeout before an idle client (status = Disconnected) is removed from the client list. (Minutes)', verbose_name='Inactive Timeout')),
                ('Vouchers_Flg', models.BooleanField(default=True, help_text='Enables voucher module.', verbose_name='Vouchers')),
                ('Pause_Resume_Flg', models.BooleanField(default=True, help_text='Enables pause/resume function.', verbose_name='Pause/Resume')),
                ('Disable_Pause_Time', models.DurationField(blank=True, default=datetime.timedelta(0), help_text='Disables Pause time button if remaining time is less than the specified time hh:mm:ss format.', null=True)),
                ('Coinslot_Pin', models.IntegerField(blank=True, help_text='Please refer raspberry/orange pi GPIO.BOARD pinout.', null=True, verbose_name='Coinslot Pin')),
                ('Light_Pin', models.IntegerField(blank=True, help_text='Please refer raspberry/orange pi GPIO.BOARD pinout.', null=True, verbose_name='Light Pin')),
                ('OpenNDS_Gateway', models.URLField(default='http://10.0.0.1:2050', help_text='Captive portal gateway server url.')),
                ('Show_User_Details', models.BooleanField(default=False, help_text='Shows client IP and MAC address on the main portal')),
                ('Insert_Coin_Sound', models.BooleanField(default=True, help_text='Enable/disable sound during insert coin.')),
            ],
            options={
                'verbose_name': 'Settings',
            },
        ),
        migrations.CreateModel(
            name='Whitelist',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('MAC_Address', models.CharField(max_length=255, unique=True, verbose_name='MAC')),
                ('Device_Name', models.CharField(blank=True, max_length=255, null=True)),
            ],
            options={
                'verbose_name': 'Allowed Client',
                'verbose_name_plural': 'Allowed Clients',
            },
        ),
        migrations.CreateModel(
            name='CoinQueue',
            fields=[
                ('Client', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, related_name='coin_queue', serialize=False, to='app.clients')),
                ('Total_Coins', models.IntegerField(blank=True, default=0, null=True)),
                ('Last_Updated', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Coin Queue',
                'verbose_name_plural': 'Coin Queue',
            },
        ),
        migrations.CreateModel(
            name='Vouchers',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('Voucher_code', models.CharField(max_length=20, unique=True)),
                ('Voucher_status', models.CharField(choices=[('Used', 'Used'), ('Not Used', 'Not Used'), ('Expired', 'Expired')], default='Not Used', max_length=25, verbose_name='Status')),
                ('Voucher_create_date_time', models.DateTimeField(auto_now_add=True, verbose_name='Created Date/Time')),
                ('Voucher_used_date_time', models.DateTimeField(blank=True, null=True, verbose_name='Used Date/Time')),
                ('Voucher_time_value', models.DurationField(default=datetime.timedelta(0), help_text='Voucher time duration in hh:mm:ss format.', verbose_name='Time Value')),
                ('Voucher_client', models.ForeignKey(blank=True, help_text='Voucher code user. * Optional', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='voucher_code', to='app.clients', verbose_name='Client')),
            ],
            options={
                'verbose_name': 'Voucher',
                'verbose_name_plural': 'Vouchers',
            },
        ),
        migrations.CreateModel(
            name='CoinSlot',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('Type', models.IntegerField(choices=[(0, 'Built In'), (1, 'Sub Vendo')], default=1)),
                ('Slot_ID', models.UUIDField(default=uuid.uuid4, unique=True)),
                ('Slot_Address', models.CharField(default='00:00:00:00:00:00', max_length=17, unique=True)),
                ('Slot_Desc', models.CharField(blank=True, max_length=50, null=True, verbose_name='Description')),
                ('Last_Updated', models.DateTimeField(auto_now=True, null=True)),
                ('Client', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='coin_slot', to='app.clients')),
                ('Setting', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='app.settings')),
            ],
            options={
                'verbose_name': 'Coin Slot',
                'verbose_name_plural': 'Coin Slot',
            },
        ),
        migrations.AddField(
            model_name='clients',
            name='Settings',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='app.settings'),
        ),
    ]
