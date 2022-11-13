from app import models
from app.utils import run_command
from paho.mqtt import publish as mqtt_publish
from django.conf import settings
import requests, json, time

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

def toggle_slot(action, light_pin):
    mqtt_settings = settings.MQTT_CONFIG
    topic = settings.MQTT_TOPICS['important_topic']

    if action == 'ON':
        # command = ['gpio', '-1', 'write', str(light_pin), str(1)]
        mqtt_publish.single(topic=topic, payload='Coinslot ON', **mqtt_settings)
    else :
        mqtt_publish.single(topic=topic, payload='Coinslot OFF', **mqtt_settings)
        # command = ['gpio', '-1', 'write', str(light_pin), str(0)]

    # run_command(command)

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