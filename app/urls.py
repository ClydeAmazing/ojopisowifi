from django.urls import path
from app import views
from app.views import * 

app_name = 'app'

urlpatterns = [
    path('portal', Portal.as_view(), name='portal'),
    path('portal/<fas>', Portal.as_view(), name="fas_decode"),
    path('pay', Pay.as_view()),
    path('commit', Commit.as_view()),
    path('gen_rc', GenerateRC.as_view()),
    path('activate', ActivateDevice.as_view()),
    path('sweep', Sweep.as_view()),
    path('voucher', GenerateVoucher.as_view()),
    path('redeem', Redeem.as_view()),
    path('eload', EloadPortal.as_view()),
]