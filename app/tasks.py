import requests, json, time
from celery import shared_task

from app.models import Clients, CoinSlot, PushNotifications
from app.utils import run_command

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
        pass

def toggle_slot(action, light_pin):
    if action == 'ON':
        command = ['gpio', '-1', 'write', str(light_pin), str(1)]
    else :
        command = ['gpio', '-1', 'write', str(light_pin), str(0)]

    run_command(command)

@shared_task
def insert_coin(client_id, slot_light_pin):
    print('Turn on light')
    toggle_slot('ON', slot_light_pin)

    while range(120): # Max number of iteration to prevent infinite loop
        try:
            client = Clients.objects.get(id=client_id)
            slot = client.coin_slot.latest()

            if slot.is_available:
                print('Turn off light')
                toggle_slot('OFF', slot_light_pin)
                break
            
            time.sleep(1)
        except (Clients.DoesNotExist, CoinSlot.DoesNotExist):
            print('Turn off light')
            toggle_slot('OFF', slot_light_pin)
            break
