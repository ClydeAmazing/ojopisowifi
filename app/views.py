from django.core.exceptions import ObjectDoesNotExist
from django.contrib import messages
from django.http import JsonResponse, HttpResponseForbidden, HttpResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.shortcuts import render, redirect
from django.views import View
from django.utils import timezone
from django.db.models import F
from django.contrib import messages
from datetime import timedelta
from getmac import getmac
from app.opw import cc, grc, fprint
from app import models

from django.http import StreamingHttpResponse
import datetime, time

from base64 import b64decode
import json


local_ip = ['::1', '127.0.0.1', '10.0.0.1']

def api_response(code):
    response = dict()

    if code == 200:
        response['code'] = code
        response['status'] = 'Success'
        response['description'] = ''

    if code == 300:
        response['code'] = code
        response['status'] = 'Error'
        response['description'] = 'Pay error.'

    if code == 400:
        response['code'] = code
        response['status'] = 'Error'
        response['description'] = 'Pay error. Slot Not Found.'

    if code == 500:
        response['code'] = code
        response['status'] = 'Error'
        response['description'] = 'Session Timeout. <strong><a href="/app/portal">Click to refresh your browser.</a></strong>'

    if code == 600:
        response['code'] = code
        response['status'] = 'Error'
        response['description'] = 'Someone is still paying. Try again.'

    if code == 700:
        response['code'] = code
        response['status'] = 'Error'
        response['description'] = 'Invalid action.'

    if code == 800:
        response['code'] = code
        response['status'] = 'Error'
        response['description'] = 'Client not found.'

    if code == 900:
        response['code'] = code
        response['status'] = 'Error'
        response['description'] = 'Unknown coin inserted.'

    if code == 110:
        response['code'] = code
        response['status'] = 'Error'
        response['description'] = 'Invalid / Used / Expired voucher code.'

    return  response

def getDeviceInfo(request):
        info = dict()
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')

        mac = getmac.get_mac_address(ip=ip)
        
        info['ip'] = ip
        info['mac'] = mac
        return info

def getClientInfo(ip, mac, fas):
    info = dict()

    if models.Whitelist.objects.filter(MAC_Address=mac).exists():
        whitelisted_flg = True
        status = 'Connected'
        time_left = timedelta(0)
        total_coins = 0
        notif_id = ''
        vouchers = None

    else:
        whitelisted_flg = False

        default_values = {
            'IP_Address': ip,
            'FAS_Session': fas
        }

        client, created = models.Clients.objects.get_or_create(MAC_Address=mac, defaults=default_values)
        if not created:
            updated = False
            if client.IP_Address != ip:
                client.IP_Address = ip
                updated = True
            if client.FAS_Session != fas:
                client.FAS_Session = fas
                updated = True
            if updated:
                client.save()

        try:
            coin_queue = client.coin_queue.get()
            total_coins = coin_queue.Total_Coins
        except ObjectDoesNotExist:
            total_coins = 0

        try:
            vouchers = models.Vouchers.objects.filter(Voucher_client=mac, Voucher_status='Not Used')
        except ObjectDoesNotExist:
            vouchers = None

        status = client.Connection_Status

        if status == 'Connected':
            time_left = client.running_time

        elif status == 'Disconnected':
            time_left = timedelta(0)

        elif status == 'Paused':
            time_left = client.Time_Left

        notif_id = client.Notification_ID

    info['ip'] = ip
    info['mac'] = mac
    info['whitelisted'] = whitelisted_flg
    info['status'] = status
    info['time_left'] = int(timedelta.total_seconds(time_left))
    info['total_coins'] = total_coins
    info['vouchers'] = vouchers
    info['appNotification_ID'] = notif_id

    return info

def getSettings():
    info = dict()
    settings = models.Settings.objects.get(pk=1)
    notif_settings = models.PushNotifications.objects.get(pk=1)

    rate_type = settings.Rate_Type
    if rate_type == 'auto':
        base_rate = settings.Base_Value
        rates = models.Rates.objects.annotate(auto_rate=F('Denom')*int(base_rate.total_seconds())).values('Denom', 'auto_rate')
        info['rates'] = rates
    else:
        info['rates'] = models.Rates.objects.all()

    if notif_settings.Enabled == True and notif_settings.app_id:
        info['push_notif'] = notif_settings
    else:
        info['push_notif'] = None

    info['rate_type'] = rate_type
    info['hotspot'] = settings.Hotspot_Name
    info['slot_timeout'] = settings.Slot_Timeout
    info['background'] = settings.BG_Image
    info['voucher_flg'] = settings.Vouchers_Flg
    info['pause_resume_flg'] = settings.Pause_Resume_Flg
    info['pause_resume_enable_time'] = 0 if not settings.Disable_Pause_Time else int(timedelta.total_seconds(settings.Disable_Pause_Time))
    info['redir_url'] = settings.Redir_Url
    info['opennds_gateway'] = settings.OpenNDS_Gateway

    return info


class Portal_(View):
    template_name = 'captive.html'

    def get(self, request, template_name=template_name):
        device_info = getDeviceInfo(request)
        ip = device_info['ip']
        mac = device_info['mac']
        info = getClientInfo(ip, mac)
        settings = getSettings()

        context = {**settings, **info}
        return render(request, template_name, context=context)

    def post(self, request):
        data = json.loads(request.body.decode("utf-8"))

        action = data.get('action')
        mac = data.get('mac')

        resp = api_response(700)

        if action == 'update_notif_id':
            notif_id = data.get('notifId', None)
            client = models.Clients.objects.get(MAC_Address=mac)
            if client.Notification_ID != notif_id and notif_id:
                client.Notification_ID = notif_id
                client.save()
                resp = api_response(200)

        return JsonResponse(resp, safe=False)


def generatePayload(fas):
    # decrypted = b64decode(b64decode(fas.encode('utf-8'))).decode('utf-8')
    decrypted =b64decode(fas.encode('utf-8')).decode('utf-8')
    fas_data = decrypted.split(', ')
    payload = dict()
    for data in fas_data:
        if '=' in data:
            parsed_data = data.split('=')
            payload[parsed_data[0]] = None if parsed_data[1] == '(null)' else parsed_data[1]
    return payload

def Stream(request):
    def event_stream():
        while True:
            time.sleep(1)
            yield 'data: The server time is: %s\n\n' % datetime.datetime.now()
    return StreamingHttpResponse(event_stream(), content_type='text/event-stream')

class Portal(View):
    template_name = 'captive.html'
    insert_coin_template = 'insert_coin.html'

    def get(self, request, fas=None):
        ip = None
        mac = None
        settings = getSettings()

        if fas:
            try:
                client = models.Clients.objects.get(FAS_Session=fas)
            except models.Clients.DoesNotExist:
                client = None

            payload = generatePayload(fas)
            if 'clientip' in payload and 'clientmac' in payload:

                if client and client.MAC_Address != payload['clientmac']:
                    return redirect(settings['opennds_gateway'])

                request.session['ip_address'] = payload['clientip']
                request.session['mac_address'] = payload['clientmac']
                request.session['fas'] = fas

                ip = payload['clientip']
                mac = payload['clientmac']

                return redirect('app:portal')
            else:
                return redirect(settings['opennds_gateway'])
        else:
            mac_address = request.session.get('mac_address', None)
            ip_address = request.session.get('ip_address', None)
            fas_session = request.session.get('fas', None)

            if mac_address and ip_address and fas_session:
                ip = ip_address
                mac = mac_address
                fas = fas_session 
            else:
                return redirect(settings['opennds_gateway'])

        info = getClientInfo(ip, mac, fas)
        context = {**settings, **info, 'fas': fas}
        return render(request, self.template_name, context=context)

    def post(self, request, fas=None):
        mac = request.session.get('mac_address', None)
        ip = request.session.get('ip_address', None)
        settings = getSettings()

        if mac and ip:
            if 'pause_resume' in request.POST:
                action = request.POST['pause_resume']
                try:
                    client = models.Clients.objects.get(MAC_Address=mac)
                    settings = getSettings()
                    pause_resume_flg = settings['pause_resume_flg']

                    if pause_resume_flg:
                        if action == 'pause':
                            pause_resume_enable_time = settings['pause_resume_enable_time']
                            client_time = timedelta.total_seconds(client.running_time)

                            if client_time > pause_resume_enable_time:
                                client.Pause()
                                messages.success(request, '<strong>Internet connection paused.</strong> Resume when you\'re ready.')

                            else:
                                # TODO: Provide a proper message
                                messages.error(request, 'Pause is not allowed.')

                        elif action == 'resume':
                            client.Connect()
                            messages.success(request, '<strong>Internet connection resumed.</strong> Enjoy browsing the internet.')
                        else:
                            # Invalid action
                            resp = api_response(700)
                            messages.error(request, resp['description'])
                    else:
                        # Invalid action
                        resp = api_response(700)
                        messages.error(request, resp['description'])

                except models.Clients.DoesNotExist:
                    # Maybe redirect to Opennds gateway

                    # Client not found error
                    resp = api_response(800)
                    messages.error(request, resp['description'])

            if 'insert_coin' in request.POST:
                try:
                    client = models.Clients.objects.get(MAC_Address = mac)
                    slot_timeout = client.Settings.Slot_Timeout
                    
                    slot_info = models.CoinSlot.objects.get(id=1)

                    if slot_info.Client == client:
                        slot_info.Last_Updated = timezone.now()
                        slot_info.save()

                        # Invoke Streaming Http Response here
                        return render(request, self.insert_coin_template, {})

                    else:
                        time_diff = timedelta.total_seconds(timezone.now()-slot_info.Last_Updated)
                        if timedelta(seconds=time_diff).total_seconds() > slot_timeout:
                            slot_info.Client = client
                            slot_info.Last_Updated = timezone.now()
                            slot_info.save()

                            # subprocess.run(['gpio', '-1', 'write', str(settings.Light_Pin), '1'])
                            # Invoke Streaming Http Response here

                        else:
                            resp = api_response(600)
                            messages.error(request, resp['description'])

                except models.Clients.DoesNotExist:
                    # probably session timed out?
                    resp = api_response(500)
                    messages.error(request, resp['description'])
        else:
            return redirect(settings['opennds_gateway'])

        return redirect('app:portal')

class Slot(View):

    def post(self, request):
        if request.is_ajax():
            mac = request.POST.get('mac')

            try:
                settings = models.Settings.objects.get(pk=1)
                timeout = settings.Slot_Timeout
                client = models.Clients.objects.get(MAC_Address=mac)

            except ObjectDoesNotExist as e:
                resp = api_response(500)

            else:
                try:
                    slot_info = models.CoinSlot.objects.get(pk=1, Client=mac)
                    slot_info.Last_Updated = timezone.now()
                    slot_info.save()

                    # subprocess.run(['gpio', '-1', 'write', str(settings.Light_Pin), '1'])
                    resp = api_response(200)

                except ObjectDoesNotExist:
                    slot_info = models.CoinSlot.objects.get(pk=1)
                    time_diff = timedelta.total_seconds(timezone.now()-slot_info.Last_Updated)
                    if timedelta(seconds=time_diff).total_seconds() > timeout:
                        slot_info.Client = mac
                        slot_info.Last_Updated = timezone.now()
                        slot_info.save()

                        # subprocess.run(['gpio', '-1', 'write', str(settings.Light_Pin), '1'])
                        resp = api_response(200)
                    else:
                        resp = api_response(600)
                
            return JsonResponse(resp, safe=False)
        else:
            raise Http404("Page not found")

@method_decorator(csrf_exempt, name='dispatch')
class Pay(View):
    def get(self, request):
        if request.is_ajax() and request.META['REMOTE_ADDR'] in local_ip:
            fp = fprint()
            dev = models.Device.objects.get(pk=1)
            if fp:
                dev.Ethernet_MAC = fp['eth0_mac']
                dev.Device_SN = fp['serial']
            dev.action = 0
            sync_time = dev.Sync_Time
            dev.save()

            settings = models.Settings.objects.values('Coinslot_Pin', 'Light_Pin', 'Slot_Timeout', 'Inactive_Timeout').get(pk=1)
            clients = models.Clients.objects.filter(Expire_On__isnull=False)
            for client in clients:
                time_diff = client.Expire_On - dev.Sync_Time
                if time_diff > timedelta(0):
                    client.Time_Left += time_diff
                    client.Expire_On = None
                    client.save()

            context = dict()
            context['device'] = {'Sync_Time': sync_time}
            context['settings'] = settings
            return JsonResponse(context, safe=False)
        else:
            raise Http404("Page not found")

    def post(self, request):
        if not request.is_ajax(): # and request.META['REMOTE_ADDR'] in local_ip:
            device = getDeviceInfo(request)
            # slot_id = request.POST.get('slot_id')
            device_MAC = device['mac']
            identifier = request.POST.get('identifier')
            pulse = int(request.POST.get('pulse', 0))

            try:
                slot_info = models.CoinSlot.objects.get(Slot_Address=device_MAC, Slot_ID=identifier)
            except ObjectDoesNotExist:
                resp = api_response(400)

            else:
                try:
                    rates = models.Rates.objects.get(Pulse=pulse)
                except ObjectDoesNotExist:
                    resp = api_response(900)
                else:
                    connected_client = slot_info.Client
                    settings = models.Settings.objects.get(pk=1)
                    timeout = settings.Slot_Timeout
                    time_diff = timedelta.total_seconds(timezone.now()-slot_info.Last_Updated)

                    if connected_client and timedelta(seconds=time_diff).total_seconds() < timeout:
                        ledger = models.Ledger()
                        ledger.Client = connected_client
                        ledger.Denomination = rates.Denom
                        ledger.Slot_No = slot_info.pk
                        ledger.save()

                        q, _ = models.CoinQueue.objects.get_or_create(Client=connected_client)
                        q.Total_Coins += rates.Denom
                        q.save()

                        slot_info.Last_Updated = timezone.now()
                        slot_info.save()

                        resp = api_response(200)
                    else:
                        resp = api_response(300)

            return JsonResponse(resp, safe=False)
        else:
            raise Http404("Page not found")

class Commit(View):
    def get(self, request):
        if not request.is_ajax():
            raise Http404("Page not found")

        else:
            data = dict()
            client = request.GET.get('mac')
            settings = models.Settings.objects.get(pk=1)
            timeout = settings.Slot_Timeout

            slot = models.CoinSlot.objects.get(pk=1, Client=client)

            time_diff = timedelta.total_seconds(timezone.now()-slot.Last_Updated)
            if timedelta(seconds=time_diff).total_seconds() > timeout:
                data['Status'] = 'Available'
                # subprocess.run(['gpio', '-1', 'write', str(settings.Light_Pin), '0'])
            else:
                data['Status'] = 'Not Available'

            try:
                queue = models.CoinQueue.objects.get(Client=client)
                data['Total_Coins'] = queue.Total_Coins
                data['Total_Time'] = int(timedelta.total_seconds(queue.Total_Time))

            except ObjectDoesNotExist:
                data['Total_Coins'] = 0
                data['Total_Time'] = 0

            return JsonResponse(data)

class Browse(View):

    def get(self, request):
        if request.is_ajax():
            ip = request.GET.get('ip')
            mac = request.GET.get('mac')

            try:
                coin_queue = models.CoinQueue.objects.get(Client=mac)
                addtl_time = coin_queue.Total_Time
                coin_queue.delete()

                push_notif = models.PushNotifications.objects.get(pk=1)
                client = models.Clients.objects.get(MAC_Address=mac)

                client.Connect(addtl_time)

                settings = models.Settings.objects.get(pk=1)
                timeout = settings.Slot_Timeout

                coin_slot = models.CoinSlot.objects.get(pk=1)
                coin_slot.Last_Updated = coin_slot.Last_Updated - timedelta(seconds=timeout)
                coin_slot.save()

                # subprocess.run(['gpio', '-1', 'write', str(settings.Light_Pin), '0'])

                resp = api_response(200)

            except ObjectDoesNotExist:
                resp = api_response(700)    

            return JsonResponse(data=resp)
        else:
            raise Http404("Page not found")

class Pause(View):
    def get(self, request):
        if request.is_ajax():
            ip = request.GET.get('ip')
            mac = request.GET.get('mac')
            action = request.GET.get('action')

            try:
                client = models.Clients.objects.get(MAC_Address=mac)

                if action == 'pause':
                    client.Pause()

                    resp = api_response(200)
                    resp['description'] = 'Paused'
                    

                elif action == 'resume':
                    client.Connect()

                    resp = api_response(200)
                    resp['description'] = 'Connected'
                    
                else:
                    resp = api_response(700)
                    

            except ObjectDoesNotExist:
                resp = api_response(800)
                

            return JsonResponse(data=resp)

        else:
            raise Http404("Page not found")

class GenerateVoucher(View):
    def get(self, request):
        client = request.GET.get("mac")
        data = dict()
        if not client:
            data['status'] = 'Error. Invalid Action'

        try:
            queue = models.CoinQueue.objects.get(Client=client)
            total_coins = queue.Total_Coins
            total_time = queue.Total_Time
            
            voucher = models.Vouchers()
            voucher.Voucher_status = 'Not Used'
            voucher.Voucher_client = client
            voucher.Voucher_time_value = total_time
            voucher.save()

            queue.delete()

            coin_slot = models.CoinSlot.objects.get(pk=1)
            coin_slot.Client = None
            coin_slot.save()

            data['voucher_code'] = voucher.Voucher_code
            data['status'] = 'OK'

        except ObjectDoesNotExist:
            data['status'] = 'Error. No coin(s) inserted.'
            
        return JsonResponse(data)

class Redeem(View):

    def post(self, request):
        if request.is_ajax():
            data = dict()
            voucher_code = request.POST.get('voucher', None)
            mac = request.POST.get('mac', None)
            try:
                voucher = models.Vouchers.objects.get(Voucher_code=voucher_code, Voucher_status = 'Not Used')
                time_value = voucher.Voucher_time_value

                if voucher.Voucher_client != mac:
                    voucher.Voucher_client = mac

                try:
                    client = models.Clients.objects.get(MAC_Address=mac)
                    client.Connect(time_value)

                    voucher.Voucher_status = 'Used'
                    voucher.save()

                except ObjectDoesNotExist:
                    resp = api_response(800)

                resp = api_response(200)
                resp['voucher_code'] = voucher.Voucher_code
                resp['voucher_time'] = time_value

            except ObjectDoesNotExist:
                resp = api_response(110)

            return JsonResponse(resp)

        else:
            raise Http404("Page not found")

# Control Section
class GenerateRC(View):
    def post(self, request):
        if request.is_ajax() and request.user.is_authenticated:
            if not cc():
                response = dict()
                rc = grc()
                response['key'] = rc.decode('utf-8')
                return  JsonResponse(response)
            else:
                return HttpResponse('Device is already activated')
        else:
            raise Http404("Page not found")

class ActivateDevice(View):
    def post(self, request):
        if not request.is_ajax and not request.user.is_authenticated:
            raise Http404("Page not found")
        
        ak = request.POST.get('activation_key', None)
        response = dict()
        if ak:
            result = cc(ak)
            if not result:
                response['message'] = 'Error'
                return JsonResponse(response)

            device = models.Device.objects.get(pk=1)
            device.Device_ID = ak
            device.save()

            response['message'] = 'Success'
            return JsonResponse(response)
        else:
            response['message'] = 'Error'
            return JsonResponse(response)

class Sweep(View):

    def get(self, request):
        if request.is_ajax() and request.META['REMOTE_ADDR'] in local_ip:
            models.Device.objects.filter(pk=1).update(Sync_Time=timezone.now())
            device = models.Device.objects.get(pk=1)
            push_notif = models.PushNotifications.objects.values('Enabled', 'app_id', 'notification_title', 'notification_message', 'notification_trigger_time').get(pk=1)
            
            settings = models.Settings.objects.get(pk=1)
            del_clients = models.Clients.objects.all()
            for del_client in del_clients:
                if del_client.Connection_Status == 'Disconnected':
                    if del_client.Expire_On:
                        diff = timezone.now() - del_client.Expire_On
                    else:
                        diff = timezone.now() - del_client.Date_Created
                    if diff > timedelta(minutes=settings.Inactive_Timeout):
                        del_client.delete()

            clients = models.Clients.objects.all().values()
            context = dict()

            context['clients'] = list(client for client in clients if client['Expire_On'] and (client['Expire_On'] - timezone.now() > timedelta(0)))
            context['system_action'] = device.action
            whitelist = models.Whitelist.objects.all().values_list('MAC_Address')
            context['whitelist'] = list(x[0] for x in whitelist)

            if push_notif['Enabled']:
                context['push_notif'] = push_notif
                push_notif_clients_qs  = models.Clients.objects.filter(Notified_Flag=False)
                push_notif_clients = list(x.Notification_ID for x in push_notif_clients_qs if x.running_time <= push_notif['notification_trigger_time'] and x.Connection_Status == 'Connected' and x.Notification_ID)
                context['push_notif_clients'] = push_notif_clients
                models.Clients.objects.filter(Notification_ID__in=push_notif_clients).update(Notified_Flag=True)
            else:
                context['push_notif'] = None
                context['push_notif_clients'] = None

            return JsonResponse(context, safe=False)
        else:
            raise Http404("Page not found")

class EloadPortal(View):
    template_name = 'admin/index.html'
    def get(self, request, template_name=template_name):
        return render(request, template_name, context={})
