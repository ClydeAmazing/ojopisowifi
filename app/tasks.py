from django.utils import timezone
from app import models
from app.utils import run_command
from datetime import timedelta
import requests, json, subprocess, ast, time

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
        pass

def shutdown_system():
    res = run_command(['sudo', 'poweroff'])
    return res

def restart_system():
    res = run_command(['sudo', 'reboot'])
    return res

def toggle_slot(action, light_pin):
    if action == 'ON':
        command = ['gpio', '-1', 'write', str(light_pin), str(1)]
    else :
        command = ['gpio', '-1', 'write', str(light_pin), str(0)]

    run_command(command)

def insert_coin(client_id, slot_light_pin):
    slot_available = False
    print('Turn on light')
    toggle_slot('ON', slot_light_pin)

    while not slot_available:
        try:
            client = models.Clients.objects.get(id=client_id)
            slot = client.coin_slot.latest()

            slot_available = slot.is_available

        except (models.Clients.DoesNotExist, models.CoinSlot.DoesNotExist):
            slot_available = True
        time.sleep(1)

    print('Turn off light')
    toggle_slot('OFF', slot_light_pin)