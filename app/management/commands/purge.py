from django.core.management.base import BaseCommand
from app.models import Clients
from django.utils import timezone
from datetime import timedelta

class Command(BaseCommand):
    help = 'Delete old clients'

    def handle(self, *args, **kwargs):
        clients = Clients.objects.all()

        count = 0

        for client in clients:
            if client.Connection_Status == 'Disconnected':
                expire_datetime = client.Expire_On if client.Expire_On else client.Date_Created
                diff = timezone.now() - expire_datetime

                if diff > timedelta(minutes=client.Settings.Inactive_Timeout):
                    client.delete()
                    count += 1

        print(f'Success! {count} client(s) purged')
