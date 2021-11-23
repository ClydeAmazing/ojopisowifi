from django.utils import timezone
from celery import shared_task
from app import models
from app.opw import fprint
from datetime import timedelta
import requests, json, subprocess, ast

@shared_task
def system_sync():
    fp = fprint()
    dev = models.Device.objects.get(pk=1)
    sync_time = dev.Sync_Time
    dev.Ethernet_MAC = fp['eth0_mac']
    dev.Device_SN = fp['serial']
    dev.action = 0 # TODO: Check if this is still relevant
    dev.save()

    clients = models.Clients.objects.filter(Expire_On__isnull=False)
    for client in clients:
        time_diff = client.Expire_On - sync_time
        if time_diff > timedelta(0):
            client.Time_Left += time_diff
            client.Expire_On = None
            client.save()

@shared_task
def built_in_payment(identifier, pulse):
    try:
        slot_info = models.CoinSlot.objects.get(Slot_ID=identifier)
    except models.CoinSlot.DoesNotExist:
        return False
    else:
        try:
            rates = models.Rates.objects.get(Pulse=pulse)
        except models.Rates.DoesNotExist:
            return False
        else:
            connected_client = slot_info.Client
            is_inserting = False

            if connected_client:
                is_inserting, _, _ = connected_client.is_inserting_coin()

            if is_inserting:
                ledger = models.Ledger()
                ledger.Client = connected_client
                ledger.Denomination = rates.Denom
                ledger.Slot_No = slot_info.pk
                ledger.save()

                q, _ = models.CoinQueue.objects.get_or_create(Client=connected_client)
                q.Total_Coins += rates.Denom
                q.save()

                slot_info.save()

                return True
            else:
                return False

@shared_task
def send_push_notif():
    try:
        clients = models.Clients.objects.filter(Notified_Flag=False)
        push_notif = models.PushNotifications.objects.get(pk=1)
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
                models.Clients.objects.filter(Notification_ID__in=player_ids).update(Notified_Flag=True)
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
    models.Device.objects.get(pk=1).save()

    clients = models.Clients.objects.all()

    for client in clients:
        if client.Connection_Status == 'Disconnected':
            expire_datetime = client.Expire_On if client.Expire_On else client.Date_Created
            diff = timezone.now() - expire_datetime

            if diff > timedelta(minutes=client.Settings.Inactive_Timeout):
                client.delete()

    ndsctl_res = subprocess.run(['sudo', 'ndsctl', 'json'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if not ndsctl_res.stderr:
        ndsctl_response = ast.literal_eval(ndsctl_res.stdout.decode('utf-8'))
        ndsctl_clients = ndsctl_response['clients']

        preauth_clients = []
        auth_clients = []

        for ndsctl_client in ndsctl_clients:
            client_status = ndsctl_clients[ndsctl_client]['state']
            if client_status == 'Preauthenticated':
                preauth_clients.append(ndsctl_client)
            elif client_status == 'Authenticated':
                auth_clients.append(ndsctl_client)

        connected_client_list = {
            c.MAC_Address:{
                'Upload_Rate': c.Upload_Rate,
                'Download_Rate': c.Download_Rate,
            }
            for c in clients if c.Connection_Status == 'Connected'
        }

        whitelists = models.Whitelist.objects.all()
        network_settings = models.Network.objects.get(pk=1)

        connected_clients = [c for c in connected_client_list]
        whitelisted_clients = [c.MAC_Address for c in whitelists]

        global_upload_rate = network_settings.Upload_Rate
        global_download_rate = network_settings.Download_Rate

        for_auth_clients = set(preauth_clients).intersection(connected_clients, whitelisted_clients)
        for_deauth_clients = set(auth_clients).difference(connected_clients, whitelisted_clients)

        # Authentication
        for client in for_auth_clients:
            if client in connected_client_list:
                client_data = connected_client_list[client]

                upload_rate = client_data['Upload_Rate'] if client_data['Upload_Rate'] > 0 else global_upload_rate
                download_rate = client_data['Download_Rate'] if client_data['Download_Rate'] > 0 else global_download_rate
            else:
                upload_rate = global_upload_rate
                download_rate = global_download_rate

            cmd = ['sudo', 'ndsctl', 'auth', client, str(0), str(upload_rate), str(download_rate)]
            ndsctl_res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            if not ndsctl_res.stderr:
                print('Client ' + client + ' successfully authenticated.')

        # Deauthentication
        for client in for_deauth_clients:
            cmd = ['sudo', 'ndsctl', 'deauth', client]
            ndsctl_res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            if not ndsctl_res.stderr:
                print('Client ' + client + ' sucessfully deauthenticated.')

    send_push_notif.delay()