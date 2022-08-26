from django.contrib import messages
from django.http import JsonResponse, Http404
from django.shortcuts import render, redirect
from django.views import View
from django.utils import timezone
from django.db.models import F
from datetime import timedelta
from app import models
from app.opw import api_response
from app.tasks import toggle_slot, insert_coin
from app.utils import get_active_clients
from base64 import b64decode
from threading import Thread as BaseThread
from django.db import close_old_connections


class Thread(BaseThread):
    def start(self):
        close_old_connections()
        super().start()

    def __init__(self, client_id, slot_light_pin):
        self.client_id = client_id
        self.slot_light_pin = slot_light_pin
        BaseThread.__init__(self)

    def run(self):
        insert_coin(self.client_id, self.slot_light_pin)

    def _bootstrap_inner(self):
        super()._bootstrap_inner()
        close_old_connections()

def is_ajax(request):
    return request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'

def getClientInfo(ip, mac, fas):
    info = dict()
    whitelisted_flg = False

    if models.Whitelist.objects.filter(MAC_Address=mac).exists():
        whitelisted_flg = True
        status = 'Connected'
        time_left = timedelta(0)
        total_coins = 0
        notif_id = ''
        vouchers = None
        slot_remaining_time = 0

    else:
        default_values = {
            'IP_Address': ip,
            'FAS_Session': fas,
            'Settings': models.Settings.objects.get(pk=1)
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
            total_coins = client.coin_queue.Total_Coins

        except models.CoinQueue.DoesNotExist:
            total_coins = 0

        try:
            vouchers = client.voucher_code.filter(Voucher_status='Not Used')
        except models.Vouchers.DoesNotExist:
            vouchers = None

        status = client.Connection_Status

        if status == 'Connected':
            time_left = client.running_time

        elif status == 'Disconnected':
            time_left = timedelta(0)

        elif status == 'Paused':
            time_left = client.Time_Left

        notif_id = client.Notification_ID

        try:
            slot = client.coin_slot.latest()
            info['insert_coin'] = True if not slot.is_available and slot.Client == client else False
            slot_remaining_time = slot.available_in_seconds
        except models.CoinSlot.DoesNotExist:
            info['insert_coin'] = False
            slot_remaining_time = 0

    info['ip'] = ip
    info['mac'] = mac
    info['whitelisted'] = whitelisted_flg
    info['status'] = status
    info['time_left'] = timedelta.total_seconds(time_left)
    info['total_time'] = client.total_time if not whitelisted_flg else 0
    info['total_coins'] = total_coins
    info['vouchers'] = vouchers
    info['appNotification_ID'] = notif_id
    info['slot_remaining_time'] = slot_remaining_time
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
    info['slot_light_pin'] = settings.Light_Pin
    info['voucher_flg'] = settings.Vouchers_Flg
    info['pause_resume_flg'] = settings.Pause_Resume_Flg
    info['pause_resume_enable_time'] = 0 if not settings.Disable_Pause_Time else int(timedelta.total_seconds(settings.Disable_Pause_Time))
    info['opennds_gateway'] = settings.OpenNDS_Gateway
    info['user_details'] = settings.Show_User_Details
    info['insert_coin_sound'] = settings.Insert_Coin_Sound

    return info

def generatePayload(fas):
    decrypted =b64decode(fas.encode('utf-8')).decode('utf-8')
    fas_data = decrypted.split(', ')
    payload = dict()
    for data in fas_data:
        if '=' in data:
            parsed_data = data.split('=')
            payload[parsed_data[0]] = None if parsed_data[1] == '(null)' else parsed_data[1]

    return payload if all([a in payload for a in ['clientip', 'clientmac']]) else False

class Portal(View):
    template_name = 'captive.html'

    def get(self, request):
        settings = getSettings()

        fas = request.session.get('fas', None)

        if not fas:
            return redirect(settings['opennds_gateway'])
        
        payload = generatePayload(fas)

        if not payload:
            return redirect(settings['opennds_gateway'])
        
        ip = payload['clientip']
        mac = payload['clientmac']
            
        info = getClientInfo(ip, mac, fas)
        context = {**settings, **info}

        return render(request, self.template_name, context=context)

    def post(self, request):
        fas_session = request.session.get('fas', None)

        settings = getSettings()

        if not fas_session:
            return redirect(settings['opennds_gateway'])

        payload = generatePayload(fas_session)
        if not payload:
            return redirect(settings['opennds_gateway'])

        mac = payload['clientmac']
            
        if 'pause_resume' in request.POST:
            action = request.POST['pause_resume']
            try:
                client = models.Clients.objects.get(MAC_Address=mac)
                pause_resume_flg = settings['pause_resume_flg']

                if not pause_resume_flg:
                    resp = api_response(700)
                    messages.error(request, resp['description'])

                    return redirect('app:portal')
                
                if action == 'pause':
                    pause_resume_enable_time = settings['pause_resume_enable_time']
                    client_time = timedelta.total_seconds(client.running_time)

                    if client_time > pause_resume_enable_time:
                        client.Pause()
                        messages.success(request, 'Internet connection paused. Resume when you are ready.')

                    else:
                        # TODO: Provide a proper message
                        messages.error(request, 'Pause is not allowed.')

                    return redirect('app:portal')

                elif action == 'resume':
                    client.Connect()
                    messages.success(request, 'Internet connection resumed. Enjoy browsing the internet.')

                    return redirect('app:portal')
                    
                else:
                    resp = api_response(700)
                    messages.error(request, resp['description'])

                    return redirect('app:portal')

            except models.Clients.DoesNotExist:

                resp = api_response(800)
                messages.error(request, resp['description'])

                return redirect('app:portal')

        if 'insert_coin' in request.POST or 'extend' in request.POST:
            success = True
            try:
                client = models.Clients.objects.get(MAC_Address=mac)
                
                # TODO: Make this coinslot assignment dynamic
                coinslot = models.CoinSlot.objects.get(id=1)

                if coinslot.is_available or coinslot.Client == client:
                    coinslot.Client = client
                    coinslot.Last_Updated = timezone.now()
                    coinslot.save()

                else:
                    resp = api_response(600)
                    messages.error(request, resp['description'])
                    success = False

            except models.Clients.DoesNotExist:
                resp = api_response(500)
                messages.error(request, resp['description'])
                success = False

            if success:
                coin_queue, created = models.CoinQueue.objects.get_or_create(Client=client)
                if not created:
                    coin_queue.save()

                thread = Thread(client.id, settings['slot_light_pin'])
                thread.start()

                messages.success(request, 'Please insert your coin(s).')
            
            return redirect('app:portal')

        if 'connect' in request.POST:
            try:
                client = models.Clients.objects.get(MAC_Address=mac)

                coin_queue = client.coin_queue
                total_coins = coin_queue.Total_Coins
                coin_queue.Claim_Queue()

                try:
                    slot = client.coin_slot.latest()
                    slot.expire_slot()
                except models.CoinSlot.DoesNotExist:
                    pass

                if total_coins > 0:
                    messages.success(request, f'₱{str(total_coins)} credited successfully. Enjoy Browsing')

            except (models.Clients.DoesNotExist, models.CoinQueue.DoesNotExist):
                pass

            return redirect('app:portal')

        if 'done' in request.POST:
            try:
                client = models.Clients.objects.get(MAC_Address=mac)

                slot = client.coin_slot.latest()
                slot.expire_slot()

            except (models.Clients.DoesNotExist, models.CoinSlot.DoesNotExist):
                pass

            return redirect('app:portal')

        if 'generate' in request.POST:
            try:
                client = models.Clients.objects.get(MAC_Address=mac)
                coin_queue = client.coin_queue
                
                voucher = models.Vouchers()
                voucher.Voucher_client = client
                voucher.Voucher_time_value = coin_queue.Total_Time
                voucher.save()

                coin_queue.delete()

                try:
                    slot = client.coin_slot.latest()
                    slot.expire_slot()
                except models.CoinSlot.DoesNotExist:
                    pass

                messages.success(request, f'Voucher code {voucher.Voucher_code} successfully generated. The new code is added to your voucher list.', extra_tags="voucher_redeem")
            
            except (models.Clients.DoesNotExist, models.CoinQueue.DoesNotExist):
                pass

            return redirect('app:portal')  

class Redeem(View):
    def post(self, request):
        fas = request.session.get('fas', None)
        voucher_code = request.POST.get('voucher_code', None)
        
        settings = getSettings()

        if fas and voucher_code:
            try:
                voucher = models.Vouchers.objects.get(Voucher_code=voucher_code.upper(), Voucher_status = 'Not Used')
                
                try:
                    client = models.Clients.objects.get(FAS_Session=fas)
                    voucher.redeem(client)

                    messages.success(request, f'Voucher code {voucher.Voucher_code} successfully redeemed!')

                except models.Clients.DoesNotExist:
                    resp = api_response(800)
                    messages.error(request, resp['description'])

            except models.Vouchers.DoesNotExist:
                resp = api_response(110)
                messages.error(request, resp['description'])
        else:
            return redirect(settings['opennds_gateway'])
            
        return redirect('app:portal')

class Commit(View):
    def get(self, request):
        if not is_ajax(request):
            raise Http404("Page not found")
        else:
            data = dict()
            fas = request.session.get('fas')

            try:
                client = models.Clients.objects.get(FAS_Session=fas)
                try:
                    slot = client.coin_slot.latest()

                    if not slot.is_available:
                        data['Status'] = 'Not Available'
                        data['Timeout'] = slot.available_in_seconds
                    else:
                        data['Status'] = 'Available'
                        data['Timeout'] = 0

                    queue = client.coin_queue

                    data['Total_Coins'] = queue.Total_Coins
                    data['Total_Time'] = int(timedelta.total_seconds(queue.Total_Time))

                except models.CoinQueue.DoesNotExist:
                    data['Total_Coins'] = 0
                    data['Total_Time'] = 0

            except (models.Clients.DoesNotExist, models.CoinSlot.DoesNotExist):
                data['Status'] = 'Error'

            return JsonResponse(data)

class Clients(View):
    def get(self, request):
        context = get_active_clients()
        return JsonResponse(context)
        
