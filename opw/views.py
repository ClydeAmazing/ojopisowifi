from django.shortcuts import redirect
from django.views import View
from django.http import HttpResponse
from app.models import Clients, Settings
from base64 import b64decode

def generatePayload(fas):
    decrypted = b64decode(fas.encode('utf-8')).decode('utf-8')
    fas_data = decrypted.split(', ')
    payload = dict()
    for data in fas_data:
        if '=' in data:
            parsed_data = data.split('=')
            payload[parsed_data[0]] = None if parsed_data[1] == '(null)' else parsed_data[1]

    return payload if all([a in payload for a in ['clientip', 'clientmac']]) else False

class Main(View):
    def get(self, request):
        fas = request.GET.get('fas', None)
        referrer_mac = request.GET.get('referrer', None)

        if fas:
            fas_payload = generatePayload(fas)
            if not fas_payload:
                return HttpResponse('Unable to retrieve device info. Please disconnect then reconnect to wifi.')

            default_values = {
                'IP_Address': fas_payload['clientip'],
                'FAS_Session': fas,
                'Settings': Settings.objects.get(pk=1)
            }

            client, created = Clients.objects.get_or_create(MAC_Address=fas_payload['mac'], defaults=default_values)

            if not created:
                updated = False
                if client.IP_Address != fas_payload['clientip']:
                    client.IP_Address = fas_payload['clientip']
                    updated = True
                if client.FAS_Session != fas:
                    client.FAS_Session = fas
                    updated = True
                if updated:
                    client.save()

            request.session['mac'] = fas_payload['clientmac']
            return redirect('app:portal')

        if referrer_mac:
            request.session['mac'] = referrer_mac

        return redirect('app:portal')
