from django.shortcuts import redirect
from django.views import View
from app.models import Clients


class Main(View):
    def get(self, request):
        fas = request.GET.get('fas', None)
        referrer_mac = request.GET.get('referrer', None)

        if fas:
            request.session['fas'] = fas

        if referrer_mac:
            client = Clients.objects.get(MAC_Address=referrer_mac)
            request.session['fas'] = client.FAS_Session

        return redirect('app:portal')
