from django.core.management.base import BaseCommand
from django.utils import timezone
from app import models
from datetime import timedelta
import requests, json, subprocess, ast, time

class Command(BaseCommand):
    help = 'Sweeper'

    def handle(self, *args, **kwargs):
        models.Device.objects.get(pk=1).save()

        clients = models.Clients.objects.all()
        settings = models.Settings.objects.get(pk=1)

        for client in clients:
            if client.Connection_Status == 'Disconnected':
                expire_datetime = client.Expire_On if client.Expire_On else client.Date_Created
                diff = timezone.now() - expire_datetime

                if diff > timedelta(minutes=client.Settings.Inactive_Timeout):
                    client.delete()

        ndsctl_res = subprocess.run(['sudo', 'ndsctl', 'json'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        if not ndsctl_res.stderr:
            try:
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
                global_upload_rate = network_settings.Upload_Rate
                global_download_rate = network_settings.Download_Rate

                connected_clients = [c for c in connected_client_list]
                whitelisted_clients = [c.MAC_Address for c in whitelists]

                all_connected_clients = set(connected_clients).union(whitelisted_clients)
                
                for_auth_clients = set(all_connected_clients).difference(auth_clients)
                for_deauth_clients = set(auth_clients).difference(all_connected_clients)

                # Authentication
                for client in for_auth_clients:
                    if client in connected_client_list:
                        client_data = connected_client_list[client]

                        upload_rate = client_data['Upload_Rate'] if client_data['Upload_Rate'] > 0 else global_upload_rate
                        download_rate = client_data['Download_Rate'] if client_data['Download_Rate'] > 0 else global_download_rate
                    else:
                        limit_whitelisted = settings.Limit_Allowed_Clients
                        upload_rate = global_upload_rate if limit_whitelisted else 0
                        download_rate = global_download_rate if limit_whitelisted else 0

                    cmd = ['sudo', 'ndsctl', 'auth', client, str(0), str(upload_rate), str(download_rate), str(0), str(0)]
                    ndsctl_res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

                    if not ndsctl_res.stderr:
                        print('Client ' + client + ' successfully authenticated.')

                    time.sleep(1)

                # Deauthentication
                for client in for_deauth_clients:
                    cmd = ['sudo', 'ndsctl', 'deauth', client]
                    ndsctl_res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

                    if not ndsctl_res.stderr:
                        print('Client ' + client + ' sucessfully deauthenticated.')

                    time.sleep(1)
            except (SyntaxError, ValueError):
                pass