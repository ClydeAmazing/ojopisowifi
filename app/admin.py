from django.contrib import admin, messages
from django.shortcuts import redirect
from django.http import HttpResponse
from django.db.models import Sum
from django.db.models.functions import TruncMonth, TruncDate
from django.urls import path
from app import models, forms
from app.opw import cc, grc, get_nds_status, speedtest

from django.contrib.auth.models import User, Group

def client_check(request):
    if request.user.is_superuser:
        return True
    else:
        return cc()

class MyAdminSite(admin.AdminSite):
    def dashboard_data(self, device):
        info = dict()
        ledger = models.Ledger.objects.all()
        sales_trend = ledger.annotate(Period=TruncDate('Date')).values('Period').annotate(Sales=Sum('Denomination')).values_list('Period', 'Sales')

        connected_count = 0
        disconnected_count = 0
        
        clients = models.Clients.objects.all()
        for client in clients:
            if client.Connection_Status == 'Connected':
                connected_count += 1
            else:
                disconnected_count += 1

        total_sales = ledger.aggregate(Sales=Sum('Denomination'))['Sales'] or 0

        info['connected_count'] = connected_count
        info['disconnected_count'] = disconnected_count
        info['total_count'] = connected_count + disconnected_count
        info['total_sales'] = total_sales
        info['sales_trend'] = list(sales_trend)

        cc_res = cc()
        if not cc_res:
            info['license_status'] = 'Not Activated'
            info['license'] = None
        else:
            info['license_status'] = 'Activated'
            info['license'] = device.Device_ID
        
        return info

    def index(self, request, extra_context=None):
        device = models.Device.objects.get(pk=1)
        extra_context = {
            'dashboard_data': self.dashboard_data(device)
        }

        if request.method == 'POST':
            if 'reset' in request.POST:
                models.Ledger.objects.all().delete()
                messages.success(request, 'Ledger is now cleared.')
            elif 'poweroff' in request.POST:
                device.action = 1
                device.save()
            elif 'reboot' in request.POST:
                device.action = 2
                device.save()
            elif 'generate' in request.POST:
                if not cc():
                    rc = grc()
                    if not rc:
                        messages.warning(request, 'Unable to generate registration code for this device.')
                    else:
                        request.session['registration_key'] = rc.decode('utf-8')
                        messages.success(request, 'Registration code generated successfully.')
                else:
                    messages.warning(request, 'Device already activated.')
            elif 'speedtest' in request.POST:
                request.session['speedtest_result'] = speedtest()
            elif all(a in request.POST for a in ['activate', 'key']):
                key = request.POST.get('key')
                result = cc(key)
                if result:
                    device.Device_ID = key
                    device.save()
                    request.session['activation'] = 'success'
                else:
                    request.session['activation'] = 'failed'

            return redirect('admin:index')

        if device.action == 1:
            return HttpResponse('Device is powering off..')
        elif device.action == 2:
            return HttpResponse('Device is rebooting..')

        registration_key = request.session.get('registration_key', None)
        if registration_key:
            extra_context['registration_key'] = registration_key
            del request.session['registration_key']

        activation_request = request.session.get('activation', None)
        if activation_request:
            extra_context['activation'] = activation_request
            del request.session['activation']

        speedtest_result = request.session.get('speedtest_result', None)
        if speedtest_result:
            extra_context['terminal'] = speedtest_result
            del request.session['speedtest_result']
        else:
            extra_context['terminal'] = get_nds_status()

        return super(MyAdminSite, self).index(request, extra_context=extra_context)

ojo_admin = MyAdminSite()

class Singleton(admin.ModelAdmin):
    change_form_template  = 'singleton_change_form.html'

    def get_urls(self):
        urls = super(Singleton, self).get_urls()
        model_name = self.model._meta.model_name
        self.model._meta.verbose_name_plural = self.model._meta.verbose_name
        url_name_prefix = '%(app_name)s_%(model_name)s' % {
            'app_name': self.model._meta.app_label,
            'model_name': model_name,
        }
        custom_urls = [
            path('',
                self.admin_site.admin_view(self.change_view),
                {'object_id': str(1)},
                name='%s_change' % url_name_prefix),
        ]
        return custom_urls + urls

class ClientsAdmin(admin.ModelAdmin):
    form = forms.ClientsForm
    list_display = ('IP_Address', 'MAC_Address', 'Device_Name', 'Connection_Status', 'Time_Left', 'running_time')
    readonly_fields = ('IP_Address', 'MAC_Address', 'Connected_On', 'Expire_On', 'Notification_ID', 'Notified_Flag', 'Date_Created', 'id', 'FAS_Session')
    actions = ['Connect', 'Disconnect', 'Pause', 'Whitelist']
    exclude = ('Settings', 'FAS_Session')

    def has_add_permission(self, *args, **kwargs):
        return False

    def changelist_view(self, request, extra_context=None):
        extra_context = {'title': 'Clients List'}
        return super(ClientsAdmin, self).changelist_view(request, extra_context=extra_context)

    def message_user(self, *args, **kwargs):
        pass

    def Connect(self, request, queryset):
        for obj in queryset:
            res = obj.Connect()
            device_name = obj.MAC_Address if not obj.Device_Name else obj.Device_Name
            if res:
                messages.add_message(request, messages.SUCCESS, 'Device {} is now connected.'. format(device_name))
            else:
                messages.add_message(request, messages.WARNING, 'Unable to connect device {}'. format(device_name))


    def Disconnect(self, request, queryset):
        for obj in queryset:
            res = obj.Disconnect()
            device_name = obj.MAC_Address if not obj.Device_Name else obj.Device_Name
            if res:
                messages.add_message(request, messages.SUCCESS, 'Device {} is now disconnected.'. format(device_name))
            else:
                messages.add_message(request, messages.WARNING, 'Device {} is already disconnected/paused.'. format(device_name))

    def Pause(self, request, queryset):
        for obj in queryset:
            res = obj.Pause()
            device_name = obj.MAC_Address if not obj.Device_Name else obj.Device_Name
            if res:
                messages.add_message(request, messages.SUCCESS, 'Device {} is now paused.'. format(device_name))
            else:
                messages.add_message(request, messages.WARNING, 'Device {} is already paused/disconnected.'. format(device_name))


    def Whitelist(self, request, queryset):      
        for obj in queryset:
            device, created = models.Whitelist.objects.get_or_create(MAC_Address=obj.MAC_Address, defaults={'Device_Name': obj.Device_Name})
            device_name = obj.MAC_Address if not obj.Device_Name else obj.Device_Name
            if created:
                messages.add_message(request, messages.SUCCESS, 'Device {} is sucessfully added to whitelisted devices'.format(device_name))
                obj.delete()
            else:
                messages.add_message(request, messages.WARNING, 'Device {} was already added on the whitelisted devices'.format(device_name))

class WhitelistAdmin(admin.ModelAdmin):
    list_display = ('MAC_Address', 'Device_Name')

    def changelist_view(self, request, extra_context=None):
        extra_context = {'title': 'Whitelisted Devices'}
        return super(WhitelistAdmin, self).changelist_view(request, extra_context=extra_context)

class CoinSlotAdmin(admin.ModelAdmin):
    form = forms.CoinSlotForm
    list_display = ('Slot_ID', 'Slot_Desc', 'Client', '_is_available')
    readonly_fields = ('Slot_ID', )

    @admin.display(description='Available', boolean=True)
    def _is_available(self, obj):
        return obj.is_available

    def message_user(self, *args):
        pass

    def save_model(self, request, obj, form, change):
        messages.add_message(request, messages.INFO, f'Slot ID: {obj.Slot_ID} updated successfully.')
        super(CoinSlotAdmin, self).save_model(request, obj, form, change)

class LedgerAdmin(admin.ModelAdmin):
    list_display = ('Date', 'Client', 'Denomination', 'Slot_No')
    list_filter = ('Client', 'Date')

    def has_add_permission(self, *args, **kwargs):
        return False

    def changelist_view(self, request, extra_context=None):
        extra_context = {'title': 'Transaction Ledger'}
        return super(LedgerAdmin, self).changelist_view(request, extra_context=extra_context)

class SettingsAdmin(Singleton, admin.ModelAdmin):
    form = forms.SettingsForm
    list_display = ('Hotspot_Name', 'Hotspot_Address', 'Slot_Timeout', 'Rate_Type', 'Base_Value', 'Inactive_Timeout', 'Coinslot_Pin', 'Light_Pin')

    def changelist_view(self, request, extra_context=None):
        extra_context = {'title': 'Wifi Settings'}
        return super(SettingsAdmin, self).changelist_view(request, extra_context=extra_context)

    def has_add_permission(self, *args, **kwargs):
        return not models.Settings.objects.exists()

    def has_delete_permission(self, *args, **kwargs):
        return False

    def has_change_permission(self, request, *args, **kwargs):
        res = client_check(request)
        return res

    def message_user(self, *args):
        pass

    def save_model(self, request, obj, form, change):
        messages.add_message(request, messages.INFO, 'Wifi Settings updated successfully.')
        super(SettingsAdmin, self).save_model(request, obj, form, change)

class NetworkAdmin(Singleton, admin.ModelAdmin):
    # form = forms.NetworkForm
    list_display = ('Edit', 'Upload_Rate', 'Download_Rate')
    exclude = ('Server_IP', 'Netmask', 'DNS_1', 'DNS_2')

    def changelist_view(self, request, extra_context=None):
        extra_context = {'title': 'Global Network Settings'}
        return super(NetworkAdmin, self).changelist_view(request, extra_context=extra_context)

    def has_add_permission(self, *args, **kwargs):
        return not models.Network.objects.exists()

    def has_delete_permission(self, *args, **kwargs):
        return False

    def has_change_permission(self, request, *args, **kwargs):
        res = client_check(request)
        return res

    def message_user(self, *args):
        pass

    def save_model(self, request, obj, form, change):
        messages.add_message(request, messages.INFO, 'Global Network Settings updated successfully.')
        super(NetworkAdmin, self).save_model(request, obj, form, change)

class CoinQueueAdmin(admin.ModelAdmin):
    list_display = ('Client', 'Total_Coins', 'Total_Time')

    def message_user(self, *args):
        pass

    def save_model(self, request, obj, form, change):
        messages.add_message(request, messages.INFO, f'Coin queue for client {obj.Client} updated successfully.')
        super(CoinQueueAdmin, self).save_model(request, obj, form, change)

class RatesAdmin(admin.ModelAdmin):
    form = forms.RatesForm
    list_display = ('Edit', 'Denom', 'Minutes', 'Minutes_Auto')
    field_order = ('Minutes', 'Denom')

    def changelist_view(self, request, extra_context=None):
        extra_context = {'title': 'Wifi Rates'}
        return super(RatesAdmin, self).changelist_view(request, extra_context=extra_context)

    def has_change_permission(self, request, *args, **kwargs):
        res = client_check(request)
        return res

    def message_user(self, *args):
        pass

    def save_model(self, request, obj, form, change):
        messages.add_message(request, messages.INFO, 'Wifi Rates updated successfully.')
        super(RatesAdmin, self).save_model(request, obj, form, change)

class DeviceAdmin(Singleton, admin.ModelAdmin):
    list_display = ('Device_SN', 'Ethernet_MAC')
    readonly_fields = ('Ethernet_MAC', 'Device_SN', 'pub_rsa', 'ca')
    # exclude = ('action',)

    def has_add_permission(self, *args, **kwargs):
        return not models.Device.objects.exists()

    def has_delete_permission(self, *args, **kwargs):
        return False

    def message_user(self, *args):
        pass

    def save_model(self, request, obj, form, change):
        messages.add_message(request, messages.INFO, 'Hardware Settings updated successfully.')
        super(DeviceAdmin, self).save_model(request, obj, form, change)

class VouchersAdmin(admin.ModelAdmin):
    form = forms.VouchersForm
    list_display = ('Voucher_code', 'Voucher_status', 'Voucher_client', 'Voucher_create_date_time', 'Voucher_used_date_time', 'Voucher_time_value')
    readonly_fields = ('Voucher_code', 'Voucher_used_date_time')

    def changelist_view(self, request, extra_context=None):
        extra_context = {'title': 'Wifi Vouchers'}
        return super(VouchersAdmin, self).changelist_view(request, extra_context=extra_context)

    def has_module_permission(self, *args, **kwargs):
        settings = models.Settings.objects.get(pk=1)
        if settings.Vouchers_Flg:
            return True
        else:
            return False

class PushNotificationsAdmin(Singleton, admin.ModelAdmin):
    form = forms.PushNotifForm
    list_display = ('Enabled', 'notification_title', 'notification_message', 'notification_trigger_time')

    def changelist_view(self, request, extra_context=None):
        extra_context = {'title': 'Push Notifications Settings'}
        return super(PushNotificationsAdmin, self).changelist_view(request, extra_context=extra_context)

    def has_add_permission(self, *args, **kwargs):
        return not models.PushNotifications.objects.exists()

    def has_delete_permission(self, *args, **kwargs):
        return False

    def has_change_permission(self, request, *args, **kwargs):
        res = client_check(request)
        return res

    def message_user(self, *args):
        pass

    def save_model(self, request, obj, form, change):
        messages.add_message(request, messages.INFO, 'Push Notification Settings updated successfully.')
        super(PushNotificationsAdmin, self).save_model(request, obj, form, change)

ojo_admin.register(models.Clients, ClientsAdmin)
ojo_admin.register(models.Whitelist, WhitelistAdmin)
ojo_admin.register(models.CoinSlot, CoinSlotAdmin)
ojo_admin.register(models.Ledger, LedgerAdmin)
ojo_admin.register(models.Settings, SettingsAdmin)
ojo_admin.register(models.Network, NetworkAdmin)
ojo_admin.register(models.CoinQueue, CoinQueueAdmin)
ojo_admin.register(models.Rates, RatesAdmin)
ojo_admin.register(models.Device, DeviceAdmin)
ojo_admin.register(models.Vouchers, VouchersAdmin)
ojo_admin.register(models.PushNotifications, PushNotificationsAdmin)
ojo_admin.register(User)
ojo_admin.register(Group)

ojo_admin.index_template = 'admin/ojo_index.html'
