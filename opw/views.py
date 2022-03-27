from django.shortcuts import redirect
from django.views import View


class Main(View):
    def get(self, request):
        fas = request.GET.get('fas', None)

        if fas:
            # return redirect('app:fas_decode', fas=base64.b64encode(fas.encode('utf-8')).decode('utf-8'))
            return redirect('app:fas_decode', fas=fas)
        else:
            return redirect('app:portal')