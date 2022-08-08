from app.models import Clients, Whitelist, Device, Network
from django.utils import timezone
from datetime import timedelta

def get_active_clients():
    Device.objects.get(pk=1).save()

    clients = Clients.objects.all()

    network_settings = Network.objects.get(pk=1)
    global_upload_rate = network_settings.Upload_Rate
    global_download_rate = network_settings.Download_Rate

    for client in clients:
        if client.Connection_Status == 'Disconnected':
            expire_datetime = client.Expire_On if client.Expire_On else client.Date_Created
            diff = timezone.now() - expire_datetime

            if diff > timedelta(minutes=client.Settings.Inactive_Timeout):
                client.delete()

    connected_client_list = {
        c.MAC_Address:{
            'u': c.Upload_Rate if c.Upload_Rate > 0 else global_upload_rate,
            'd': c.Download_Rate if c.Download_Rate > 0 else global_download_rate,
        }
        for c in clients if c.Connection_Status == 'Connected'
    }

    whitelists = Whitelist.objects.all()

    for c in whitelists:
        connected_client_list[c.MAC_Address] = {
            'u': c.Upload_Rate if c.Upload_Rate > 0 else global_upload_rate,
            'd': c.Download_Rate if c.Download_Rate > 0 else global_download_rate,
        }
    
    data = {
            'clients': connected_client_list,
        }
    return data