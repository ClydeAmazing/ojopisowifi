from django.core.management.base import BaseCommand
from app.models import Device, Clients
from app.opw import fprint
from datetime import timedelta

class Command(BaseCommand):
    help = 'Initializes the application on startup'

    def handle(self, *args, **kwargs):
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