from django.core.exceptions import ValidationError
from django.db import models
from datetime import timedelta
from django.utils import timezone
from django.core.validators import MaxValueValidator, MinValueValidator
from django.utils import duration
import string, random, os, math, uuid

class Settings(models.Model):
    rate_type_choices = (
        ('auto', 'Minutes/Peso'),
        ('manual', 'Custom Rate'),
    )

    def get_image_path(instance, filename):
        return os.path.join(str(instance.id), filename)

    Hotspot_Name = models.CharField(max_length=255)
    Hotspot_Address = models.CharField(max_length=255, null=True, blank=True)
    Slot_Timeout = models.PositiveIntegerField(help_text='Slot timeout in seconds. Default is 15', default=15, validators=[MinValueValidator(1), MaxValueValidator(30)])
    Rate_Type = models.CharField(max_length=25, default="auto", choices=rate_type_choices, help_text='Select "Minutes/Peso" to use  Minutes / Peso value, else use "Custom Rate" to manually setup Rates based on coin value.')
    Base_Value = models.DurationField(default=timezone.timedelta(minutes=0), verbose_name='Minutes / Peso', help_text='Base time value for each peso. Specify in hh:mm:ss format. Applicable only if Rate Type is Minutes/Peso')
    Inactive_Timeout = models.IntegerField(verbose_name='Inactive Timeout', help_text='Timeout before an idle client (status = Disconnected) is removed from the client list. (Minutes)')
    Vouchers_Flg = models.BooleanField(verbose_name='Vouchers', default=True, help_text='Enables voucher module.')
    Pause_Resume_Flg = models.BooleanField(verbose_name='Pause/Resume', default=True, help_text='Enables pause/resume function.')
    Disable_Pause_Time = models.DurationField(default=timezone.timedelta(minutes=0), null=True, blank=True, help_text='Disables Pause time button if remaining time is less than the specified time hh:mm:ss format.')
    Coinslot_Pin = models.IntegerField(verbose_name='Coinslot Pin', help_text='Please refer raspberry/orange pi GPIO.BOARD pinout.', null=True, blank=True)
    Light_Pin = models.IntegerField(verbose_name='Light Pin', help_text='Please refer raspberry/orange pi GPIO.BOARD pinout.', null=True, blank=True)
    OpenNDS_Gateway = models.URLField(max_length=200, default='http://10.0.0.1:2050', help_text='Captive portal gateway server url.')
    Show_User_Details = models.BooleanField(default=False, help_text='Shows client IP and MAC address on the main portal')
    Insert_Coin_Sound = models.BooleanField(default=True, help_text='Enable/disable sound during insert coin.')

    class Meta:
        verbose_name = 'Settings'

    def __str__(self):
        return 'Settings'

class Clients(models.Model):
    IP_Address = models.CharField(max_length=15, verbose_name='IP')
    MAC_Address = models.CharField(max_length=255, verbose_name='MAC Address', unique=True)
    Device_Name = models.CharField(max_length=255, verbose_name='Device Name', null=True, blank=True)
    Time_Left = models.DurationField(default=timezone.timedelta(minutes=0))
    Connected_On = models.DateTimeField(null=True, blank=True)
    Expire_On = models.DateTimeField(null=True, blank=True)
    Upload_Rate = models.IntegerField(help_text='Specify client internet upload bandwidth in Kbps. No value = unlimited bandwidth', default=0)
    Download_Rate = models.IntegerField(help_text='Specify client internet download bandwidth in Kbps. No value = unlimited bandwidth', default=0)
    Notification_ID = models.CharField(verbose_name = 'Notification ID', max_length=255, null=True, blank = True)
    Notified_Flag = models.BooleanField(default=False)
    Date_Created = models.DateTimeField(auto_now_add=True)
    FAS_Session = models.CharField(max_length=500, unique=True)
    Settings = models.ForeignKey(Settings, on_delete=models.CASCADE)

    @property
    def running_time(self):
        if not self.Expire_On:
            return timedelta(0)
        else:
            running_time = self.Expire_On - timezone.now()
            if running_time < timedelta(0):
                return timedelta(0)
            else:
                return running_time

    @property
    def total_time(self):
        if self.Expire_On and self.Connected_On:
            return timedelta.total_seconds(self.Expire_On - self.Connected_On)
        else:
            return 0

    @property
    def Connection_Status(self):
        if self.running_time > timedelta(0):
            return 'Connected'
        else:
            if self.Time_Left > timedelta(0):
                return 'Paused'
            else:
                return 'Disconnected'

    def credit_amount(self, amount):
        self.coin_queue.Total_Coins += amount
        self.coin_queue.save()

    def Connect(self, add_time = timedelta(0)):
        total_time = self.Time_Left + add_time
        success_flag = False
        if total_time > timedelta(0):
            if self.running_time > timedelta(0):
                self.Expire_On = self.Expire_On + total_time
            else:
                self.Expire_On = timezone.now() + total_time

            self.Connected_On = timezone.now()
            self.Time_Left = timedelta(0)

            push_notif = PushNotifications.objects.get(pk=1)
            push_trigger_time = push_notif.notification_trigger_time

            if (total_time + self.running_time) > push_trigger_time and self.Notified_Flag == True:
                self.Notified_Flag = False

            self.save()

            success_flag = True
        return success_flag

    def Disconnect(self):
        success_flag = False
        if self.Connection_Status == 'Connected':
            self.Expire_On = None
            self.Connected_On = None
            self.Time_Left = timedelta(0)
            self.Notified_Flag = False
            self.save()
            success_flag = True
        return success_flag

    def Pause(self):
        success_flag = False
        if self.Connection_Status == 'Connected':
            self.Time_Left = self.running_time
            self.Expire_On = None
            self.save()
            success_flag = True
        return success_flag

    class Meta:
        verbose_name = 'Client'
        verbose_name_plural = 'Clients'

    def __str__(self):
        return str(self.IP_Address) + ' | ' + str(self.MAC_Address)

class Whitelist(models.Model):
    MAC_Address = models.CharField(max_length=255, verbose_name='MAC', unique=True)
    Device_Name = models.CharField(max_length=255, null=True, blank=True)
    Upload_Rate = models.IntegerField(help_text='Specify client internet upload bandwidth in Kbps. No value = unlimited bandwidth', default=0)
    Download_Rate = models.IntegerField(help_text='Specify client internet download bandwidth in Kbps. No value = unlimited bandwidth', default=0)

    class Meta:
        verbose_name = 'Allowed Client'
        verbose_name_plural = 'Allowed Clients'

    def __str__(self):
        name =  self.MAC_Address if not self.Device_Name else self.Device_Name
        return 'Device: ' + name

class Ledger(models.Model):
    Date = models.DateTimeField(verbose_name="Transaction Date", auto_now_add=True)
    Client = models.CharField(max_length=50)
    Denomination = models.IntegerField()
    Slot_No = models.IntegerField()

    class Meta:
        verbose_name = 'Ledger'
        verbose_name_plural = 'Ledger'

    def __str__(self):
        return 'Transaction no: ' + str(self.pk)

class CoinSlot(models.Model):
    TYPE_CHOICES = (
        (0, 'Built In'),
        (1, 'Sub Vendo')
    )

    Client = models.ForeignKey(Clients, on_delete=models.SET_NULL, null=True, blank=True, related_name='coin_slot')
    Setting = models.ForeignKey(Settings, on_delete=models.CASCADE)
    Type = models.IntegerField(default=1, choices=TYPE_CHOICES)
    Slot_ID = models.UUIDField(unique=True, default=uuid.uuid4)
    Slot_Address = models.CharField(unique=True, max_length=17, default='00:00:00:00:00:00')
    Slot_Desc = models.CharField(max_length=50, null=True, blank=True, verbose_name='Description')
    Last_Updated = models.DateTimeField(null=True, blank=True, auto_now_add=True)

    @property
    def available_in_seconds(self):
        slot_timeout = self.Setting.Slot_Timeout

        time_since_last_updated = timedelta.total_seconds(timezone.now()-self.Last_Updated)
        remaining_time = slot_timeout - time_since_last_updated

        return 0 if remaining_time <= 0 else remaining_time

    @property
    def is_available(self):
        slot_timeout = self.Setting.Slot_Timeout
        time_since_last_updated = timedelta.total_seconds(timezone.now()-self.Last_Updated)

        if time_since_last_updated >= slot_timeout or not self.Client:
            return True
        else:
            return False

    def expire_slot(self):
        self.Client = None
        self.Last_Updated = timezone.now()
        self.save()

    def save(self, *args, **kwargs):
        if self._state.adding:
            self.Slot_ID = self.generate_code()
        super(CoinSlot, self).save(*args, **kwargs)

    class Meta:
        verbose_name = 'Coin Slot'
        verbose_name_plural = 'Coin Slot'
        get_latest_by = 'Last_Updated'

    def __str__(self):
        return 'Slot no: ' + str(self.pk)

class Rates(models.Model):
    Edit = "Edit"
    Denom = models.IntegerField(verbose_name='Denomination', help_text="Coin denomination corresponding to specified coinslot pulse.")
    Pulse = models.IntegerField(blank=True, null=True, help_text="Coinslot pulse count corresponding to coin denomination. Leave it blank for promotional rates.")
    Minutes = models.DurationField(verbose_name='Duration (Custom)', default=timezone.timedelta(minutes=0), help_text='Internet access duration in hh:mm:ss format')

    @property
    def Minutes_Auto(self):
        settings = Settings.objects.get(pk=1)
        return timedelta(seconds=timedelta.total_seconds(self.Denom * settings.Base_Value))

    Minutes_Auto.fget.short_description = "Duration (Auto)"

    class Meta:
        verbose_name = "Rate"
        verbose_name_plural = "Rates"

    def __str__(self):
        return str(self.Denom)

class CoinQueue(models.Model):
    Client = models.OneToOneField(Clients, on_delete=models.CASCADE, primary_key=True, related_name='coin_queue')
    Total_Coins = models.IntegerField(null=True, blank=True, default=0)
    Last_Updated = models.DateTimeField(auto_now=True)

    @property
    def Total_Time(self):
        settings = self.Client.Settings
        rate_type = settings.Rate_Type
        base_value = settings.Base_Value
        total_coins = self.Total_Coins
        total_time = timedelta(0)

        if rate_type == 'manual':
            rates = Rates.objects.all().order_by('-Denom')
            for rate in rates:
                multiplier = math.floor(total_coins/rate.Denom)
                if multiplier > 0:
                    total_coins = total_coins - (rate.Denom * multiplier)
                    total_time = total_time + (rate.Minutes * multiplier)
        
        if rate_type == 'auto':
            total_time = base_value * total_coins
        
        return total_time

    def add_to_queue(self, denom):
        self.Total_Coins += denom
        self.save()

        try:
            slot = self.Client.coin_slot.latest()
            slot.Last_Updated = timezone.now()
            slot.save()
        except (Clients.DoesNotExist, CoinSlot.DoesNotExist):
            pass

    def Claim_Queue(self):
        if self.Total_Coins > 0:
            self.Client.Connect(self.Total_Time)
        self.delete()

    class Meta:
        verbose_name = 'Coin Queue'
        verbose_name_plural = 'Coin Queue'

    def __str__(self):
        return 'Queue: ' + self.Client.MAC_Address

class Network(models.Model):
    Edit = "Edit"
    Server_IP = models.GenericIPAddressField(verbose_name='Server IP', protocol='IPv4', default='10.0.0.1')
    Netmask = models.GenericIPAddressField(protocol='IPv4', default='255.255.255.0')
    DNS_1 = models.GenericIPAddressField(protocol='IPv4', verbose_name='DNS 1', default='8.8.8.8')
    DNS_2 = models.GenericIPAddressField(protocol='IPv4', verbose_name='DNS 2 (Optional)', default='8.8.4.4', null=True, blank=True)
    Upload_Rate = models.IntegerField(verbose_name='Upload Limit', help_text='Specify global internet upload bandwidth in Kbps. 0 = unlimited bandwidth', default=0)
    Download_Rate = models.IntegerField(verbose_name='Download Limit', help_text='Specify global internet download bandwidth in Kbps. 0 = unlimited bandwidth', default=0)
    Limit_Allowed_Clients = models.BooleanField(default=False, help_text='Check if bandwith limiting should also be applied to Allowed/Whitelisted devices.')

    class Meta:
        verbose_name = 'Networking'

    def __str__(self):
        return 'Network Settings'

class Vouchers(models.Model):
    status_choices = (
        ('Used', 'Used'),
        ('Not Used', 'Not Used'),
        ('Expired', 'Expired')
    )

    def generate_code(self, size=6):
        found = False
        random_code = None

        while not found:
            random_code = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(size))
            count = Vouchers.objects.filter(Voucher_code=random_code).count()
            if count == 0:
                found = True

        return random_code

    Voucher_code = models.CharField(max_length=20, unique=True)
    Voucher_status = models.CharField(verbose_name='Status', max_length=25, choices=status_choices, default='Not Used')
    Voucher_client = models.ForeignKey(Clients, on_delete=models.CASCADE, null=True, blank=True, verbose_name='Client', help_text='Voucher code user. * Optional', related_name='voucher_code')
    Voucher_create_date_time = models.DateTimeField(verbose_name='Created Date/Time', auto_now_add=True)
    Voucher_used_date_time = models.DateTimeField(verbose_name='Used Date/Time', null=True, blank=True)
    Voucher_time_value = models.DurationField(verbose_name='Time Value', default=timezone.timedelta(minutes=0), help_text='Voucher time duration in hh:mm:ss format.')

    def redeem(self, client):
        client.Connect(self.Voucher_time_value)
        if self.Voucher_client != client:
            self.Voucher_client = client
        self.Voucher_status = 'Used'
        self.save()

    def save(self, *args, **kwargs):
        if self.Voucher_status == 'Used':
             self.Voucher_used_date_time = timezone.now()

        if self.Voucher_status == 'Not Used':
            self.Voucher_used_date_time = None

        if self._state.adding:
            self.Voucher_code = self.generate_code()

        super(Vouchers, self).save(*args, **kwargs)

    class Meta:
        verbose_name = 'Voucher'
        verbose_name_plural = 'Vouchers'

    def __str__(self):
        return self.Voucher_code

class Device(models.Model):
    Device_ID = models.CharField(max_length=255, null=True, blank=True)
    Ethernet_MAC = models.CharField(max_length=50, null=True, blank=True)
    Device_SN = models.CharField(max_length=50, null=True, blank=True)
    pub_rsa = models.TextField(null=False, blank=False)
    ca = models.CharField(max_length=200, unique=True)
    action = models.IntegerField(default=0)
    Sync_Time = models.DateTimeField(auto_now=True, null=True, blank=True)

    class Meta:
        verbose_name = 'Hardware'

    def __str__(self):
        return 'Hardware Settings'

class PushNotifications(models.Model):
    Enabled = models.BooleanField(default=False, verbose_name='Enable')
    app_id = models.CharField(verbose_name = "OneSignal App ID", max_length=255, null=True, blank=True)
    notification_title = models.CharField(verbose_name="Notification Title", max_length=255, null=True, blank=True)
    notification_message = models.CharField(verbose_name="Notification Message", max_length=255, null=True, blank=True)
    notification_trigger_time = models.DurationField(verbose_name="Notification Trigger", default=timezone.timedelta(minutes=0), help_text="Notification will fire when time is equal to the specified trigger time. Format: hh:mm:ss", null=True, blank=True)

    class Meta:
        verbose_name = "Push Notifications"

    def __str__(self):
        return "Push Notification Settings"