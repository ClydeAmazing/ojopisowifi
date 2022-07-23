from django.contrib import messages
from django.http import JsonResponse, Http404
from django.shortcuts import render, redirect
from django.views import View
from django.utils import timezone
from django.db.models import F
from datetime import timedelta
from app import models
from app.opw import api_response
from app.tasks import toggle_slot
from base64 import b64decode

# This is a test change

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
            coin_queue = models.CoinQueue.objects.get(Client=client)
            total_coins = coin_queue.Total_Coins

        except models.CoinQueue.DoesNotExist:
            total_coins = 0

        try:
            vouchers = models.Vouchers.objects.filter(Voucher_client=client, Voucher_status='Not Used')
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

        is_inserting, _, slot_remaining_time = client.is_inserting_coin()

    info['ip'] = ip
    info['mac'] = mac
    info['whitelisted'] = whitelisted_flg
    info['status'] = status
    info['time_left'] = timedelta.total_seconds(time_left)
    info['total_time'] = client.total_time
    info['total_coins'] = total_coins
    info['vouchers'] = vouchers
    info['appNotification_ID'] = notif_id
    info['insert_coin'] = is_inserting
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
                # Maybe redirect to Opennds gateway

                resp = api_response(800)
                messages.error(request, resp['description'])

                return redirect('app:portal')

        if 'insert_coin' in request.POST or 'extend' in request.POST:
            success = True
            try:
                client = models.Clients.objects.get(MAC_Address=mac)
                
                # TODO: Make this coinslot assignment dynamic
                coinslot = models.CoinSlot.objects.get(id=1)

                if not coinslot.Client or coinslot.Client == client: 
                    coinslot.Client = client
                    coinslot.save()
                else:
                    time_diff = timedelta.total_seconds(timezone.now()-coinslot.Last_Updated)
                    if timedelta(seconds=time_diff).total_seconds() > settings['slot_timeout']:
                        coinslot.Client = client
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

                # Activate coinslot
                # toggle_slot.delay(1, settings['slot_light_pin'])

                messages.success(request, 'Please insert your coin(s).')
            
            return redirect('app:portal')

        if 'connect' in request.POST:
            try:
                client = models.Clients.objects.get(MAC_Address=mac)

                coin_queue = models.CoinQueue.objects.get(Client=client)
                total_coins = coin_queue.Total_Coins
                coin_queue.Claim_Queue()

                client.expire_slot()

                # Deactivate coinslot
                toggle_slot.delay(0, settings['slot_light_pin'])

                if total_coins > 0:
                    messages.success(request, f'₱{str(total_coins)} credited successfully. Enjoy Browsing')

            except (models.Clients.DoesNotExist, models.CoinQueue.DoesNotExist):
                resp = api_response(700)
                messages.error(request, resp['description'])

            return redirect('app:portal')

        if 'done' in request.POST:
            try:
                client = models.Clients.objects.get(MAC_Address=mac)
                client.expire_slot()

                # Deactivate coinslot
                # toggle_slot.delay(0, settings['slot_light_pin'])

            except (models.Clients.DoesNotExist):
                resp = api_response(700)
                messages.error(request, resp['description'])

            return redirect('app:portal')

        if 'generate' in request.POST:
            try:
                client = models.Clients.objects.get(MAC_Address=mac)
                coin_queue = models.CoinQueue.objects.get(Client=client)
                total_time = coin_queue.Total_Time
                
                voucher = models.Vouchers()
                voucher.Voucher_status = 'Not Used'
                voucher.Voucher_client = client
                voucher.Voucher_time_value = total_time
                voucher.save()

                coin_queue.delete()

                client.expire_slot()
                # Deactivate coinslot
                # toggle_slot.delay(0, settings['slot_light_pin'])

                messages.success(request, f'Voucher code {voucher.Voucher_code} successfully generated. The new code is added to your voucher list.', extra_tags="voucher_redeem")
            except (models.Clients.DoesNotExist, models.CoinQueue.DoesNotExist):
                resp = api_response(700)
                messages.error(request, resp['description'])

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
                    is_inserting, _, slot_remaining_time = client.is_inserting_coin()

                    if is_inserting:
                        data['Status'] = 'Not Available'
                        data['Timeout'] = slot_remaining_time

                    else:
                        data['Status'] = 'Available'
                        data['Timeout'] = 0

                    queue = models.CoinQueue.objects.get(Client=client)

                    data['Total_Coins'] = queue.Total_Coins
                    data['Total_Time'] = int(timedelta.total_seconds(queue.Total_Time))

                except models.CoinQueue.DoesNotExist:
                    data['Total_Coins'] = 0
                    data['Total_Time'] = 0

            except (models.Clients.DoesNotExist, models.CoinSlot.DoesNotExist):
                data['Status'] = 'Error'

            return JsonResponse(data)