from django.shortcuts import redirect
from django.views import View


class Main(View):
    def get(self, request):
        fas = request.GET.get('fas', None)

        if fas:
            request.session['fas'] = fas
        return redirect('app:portal')
