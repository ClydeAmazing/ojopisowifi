from django.utils import timezone
from celery import shared_task
from app.models import CoinSlot, Rates, Ledger, CoinQueue, Clients, PushNotifications, Device, Settings
from app.opw import fprint
from datetime import timedelta
import requests, json, subprocess

@shared_task
def system_sync():
    fp = fprint()
    dev = Device.objects.get(pk=1)
    sync_time = dev.Sync_Time
    dev.Ethernet_MAC = fp['eth0_mac']
    dev.Device_SN = fp['serial']
    dev.action = 0 # TODO: Check if this is still relevant
    dev.save()

    clients = Clients.objects.filter(Expire_On__isnull=False)
    for client in clients:
        time_diff = client.Expire_On - sync_time
        if time_diff > timedelta(0):
            client.Time_Left += time_diff
            client.Expire_On = None
            client.save()

@shared_task
def built_in_payment(identifier, pulse):
    # device_MAC = request.POST.get('mac_address')
    # identifier = request.POST.get('identifier')
    # pulse = int(request.POST.get('pulse', 0))

    try:
        slot_info = CoinSlot.objects.get(Slot_ID=identifier)
    except CoinSlot.DoesNotExist:
        return False
        # resp = api_response(400)
    else:
        try:
            rates = Rates.objects.get(Pulse=pulse)
        except Rates.DoesNotExist:
            return False
            # resp = api_response(900)
        else:
            connected_client = slot_info.Client
            is_inserting = False

            if connected_client:
                is_inserting, _, _ = connected_client.is_inserting_coin()

            if is_inserting:
                ledger = Ledger()
                ledger.Client = connected_client
                ledger.Denomination = rates.Denom
                ledger.Slot_No = slot_info.pk
                ledger.save()

                q, _ = CoinQueue.objects.get_or_create(Client=connected_client)
                q.Total_Coins += rates.Denom
                q.save()

                slot_info.save()

                # resp = api_response(200)
                return True
            else:
                return False
                # resp = api_response(300)

@shared_task
def send_push_notif():
    try:
        clients = Clients.objects.filter(Notified_Flag=False)
        push_notif = PushNotifications.objects.get(pk=1)
        if clients and push_notif.Enabled:
            app_id = push_notif.app_id
            notif_title = push_notif.notification_title
            notif_message = push_notif.notification_message
            player_ids = list(x.Notification_ID for x in clients if x.running_time <= push_notif['notification_trigger_time'] and x.Connection_Status == 'Connected' and x.Notification_ID)
            payload = {
                    "app_id": app_id,
                    "include_player_ids": player_ids,
                    "contents": {"en": notif_message},
                    "headings": {"en": notif_title}
                    }

            header = {"Content-Type": "application/json; charset=utf-8"}
            host = "https://onesignal.com/api/v1/notifications"
            response = requests.post(host, headers=header, data=json.dumps(payload))
            if response.status_code == 200:
                Clients.objects.filter(Notification_ID__in=player_ids).update(Notified_Flag=True)
    except Exception:
        pass # hahaha! A mortal sin. Maybe log this in the future

@shared_task
def shutdown_system():
    res = subprocess.run(['sudo', 'poweroff'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if res.stderr:
	    print(res.stderr.decode('utf-8'))

@shared_task
def restart_system():
    res = subprocess.run(['sudo', 'reboot'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if res.stderr:
        print(res.stderr.decode('utf-8'))

@shared_task
def sweep():
    Device.objects.get(pk=1).save()

    clients = Clients.objects.all()
    for client in clients:
        if client.Connection_Status == 'Disconnected':
            expire_datetime = client.Expire_On if client.Expire_On else client.Date_Created
            diff = timezone.now() - expire_datetime

            if diff > timedelta(minutes=client.Settings.Inactive_Timeout):
                client.delete()

    # whitelist = models.Whitelist.objects.all().values_list('MAC_Address')
    # Work on whitelisted clients

    # TODO: Activate/Deactivate clients based on current status using NDSCTL commands
    # res = subprocess.run(['sudo', 'ndsctl', 'json'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    # if not res.stderr:
    #     Authentication

    #     Deauthentication
    #     pass

    # Sending push notifications
    send_push_notif.delay()