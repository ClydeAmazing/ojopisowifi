from django.shortcuts import redirect
from django.views import View
from app.models import Clients


class Main(View):
    def get(self, request):
        fas = request.GET.get('fas', None)
        referrer_mac = request.GET.get('referrer', None)

        if fas:
            request.session['fas'] = fas
            return redirect('app:portal')

        if referrer_mac:
            try:
                client = Clients.objects.get(MAC_Address=referrer_mac)
                request.session['fas'] = client.FAS_Session
            except Clients.DoesNotExist:
                pass

        return redirect('app:portal')
