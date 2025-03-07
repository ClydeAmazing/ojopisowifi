from django.contrib import messages
from django.http import JsonResponse, Http404
from django.shortcuts import render, redirect
from django.views import View
from django.utils import timezone
from django.db.models import F
from datetime import timedelta
from app import models
from app.tasks import insert_coin
from app.utils import get_active_clients

def is_ajax(request):
    return request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'

def getClientInfo(mac):
    if models.Whitelist.objects.filter(MAC_Address=mac).exists():
        client_info = {
            'mac': mac,
            'ip': None,
            'whitelisted': True,
            'status': 'Connected',
            'time_left': 0,
            'total_time': 0,
            'total_coins': 0,
            'vouchers': None,
            'appNotification_ID': '',
            'slot_remaining_time': 0
        }

    else:
        try:
            client = models.Clients.objects.get(MAC_Address=mac)

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
                insert_coin_flg = True if not slot.is_available and slot.Client == client else False
                slot_remaining_time = slot.available_in_seconds
            except models.CoinSlot.DoesNotExist:
                insert_coin_flg = False
                slot_remaining_time = 0

            client_info = {    
                'mac': mac,
                'ip': client.IP_Address,
                'whitelisted': False,
                'status': status,
                'time_left': timedelta.total_seconds(time_left),
                'total_time': client.total_time,
                'total_coins': total_coins,
                'vouchers': vouchers,
                'appNotification_ID': notif_id,
                'slot_remaining_time': slot_remaining_time,
                'insert_coin': insert_coin_flg
            }
        except models.Clients.DoesNotExist:
            client_info = {}

    return client_info

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

class Portal(View):
    template_name = 'captive.html'

    def get(self, request):
        settings = getSettings()
        mac = request.session.get('mac', None)

        if not mac:
            return redirect(settings['opennds_gateway'])
            
        client_info = getClientInfo(mac)

        if not client_info:
            return redirect(settings['opennds_gateway'])

        context = {**settings, **client_info}
        return render(request, self.template_name, context=context)

    def post(self, request):
        settings = getSettings()
        mac = request.session.get('mac', None)

        if not mac:
            return redirect(settings['opennds_gateway'])
            
        if 'pause_resume' in request.POST:
            action = request.POST['pause_resume']
            try:
                client = models.Clients.objects.get(MAC_Address=mac)
            except models.Clients.DoesNotExist:
                messages.error(request, 'Unable to identify client.')
                return redirect('app:portal')

            can_pause = settings['pause_resume_flg']
            
            if action == 'pause':
                if not can_pause:
                    # TODO: Provide a proper message
                    messages.error(request, 'Pause is not allowed.')
                    return redirect('app:portal')

                pause_resume_enable_time = settings['pause_resume_enable_time']
                client_time = timedelta.total_seconds(client.running_time)

                if client_time > pause_resume_enable_time:
                    client.Pause()
                    messages.success(request, 'Internet connection paused. Resume when you are ready.')

                else:
                    # TODO: Provide a proper message
                    messages.error(request, 'Pause is not allowed.')

                return redirect('app:portal')

            if action == 'resume':
                if client.Connect():
                    messages.success(request, 'Internet connection resumed. Enjoy browsing the internet.')

                return redirect('app:portal')

            # Any other actions is invalid
            messages.error(request, 'Invalid action.')
            return redirect('app:portal')

        if 'insert_coin' in request.POST or 'extend' in request.POST:
            try:
                client = models.Clients.objects.get(MAC_Address=mac)
                
                # TODO: Make this coinslot assignment dynamic
                coinslot = models.CoinSlot.objects.get(id=1)

                if coinslot.is_available or coinslot.Client == client:
                    coinslot.Client = client
                    coinslot.Last_Updated = timezone.now()
                    coinslot.save()

                    coin_queue, created = models.CoinQueue.objects.get_or_create(Client=client)
                    if not created:
                        coin_queue.save()

                    # Check coin slot and turn off slot after the delay
                    insert_coin.delay(client.id, settings['slot_light_pin'])

                    messages.success(request, 'Please insert your coin(s).')
                else:
                    messages.error(request, 'Someone is still paying. Please try again later.')
                    
                return redirect('app:portal')

            except models.Clients.DoesNotExist:
                error_message = 'Session Timeout. <strong><a href="/app/portal">Click to refresh your browser.</a></strong>'
                messages.error(request, error_message)
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
        mac = request.session.get('mac', None)
        voucher_code = request.POST.get('voucher_code', None)
        
        settings = getSettings()

        if not mac:
            return redirect(settings['opennds_gateway'])
        
        if not voucher_code:
            messages.error(request, 'Please enter Voucher Code')
            return redirect('app:portal')

        try:
            client = models.Clients.objects.get(MAC_Address=mac)
        except models.Clients.DoesNotExist:
            return redirect(settings['opennds_gateway'])

        try:
            voucher = models.Vouchers.objects.get(Voucher_code=voucher_code.upper(), Voucher_status = 'Not Used')
        except models.Vouchers.DoesNotExist:
            messages.error(request, 'Invalid / Used / Expired voucher code.')
            return redirect('app:portal')

        voucher.redeem(client)
        messages.success(request, f'Voucher code {voucher.Voucher_code} successfully redeemed!')
        return redirect('app:portal')

class Commit(View):
    def get(self, request):
        if not is_ajax(request):
            raise Http404("Page not found")
        else:
            data = dict()
            mac = request.session.get('mac')

            try:
                client = models.Clients.objects.get(MAC_Address=mac)
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
        
