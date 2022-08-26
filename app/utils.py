from app.models import Clients, Whitelist, Device, Network
import subprocess

def run_command(command):
    try:
        res = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return res
    except FileNotFoundError:
        return None

def get_active_clients():
    Device.objects.get(pk=1).save()

    clients = Clients.objects.all()

    network_settings = Network.objects.get(pk=1)
    global_upload_rate = network_settings.Upload_Rate
    global_download_rate = network_settings.Download_Rate

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