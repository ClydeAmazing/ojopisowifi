from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.urls import path
from app import views
from app.views import * 

app_name = 'app'

urlpatterns = [
    # path('', Portal.as_view(), name="index"),
    path('portal', Portal.as_view(), name='portal'),
    path('portal/<fas>', Portal.as_view(), name="fas_decode"),
    # path('portal', never_cache(Portal_.as_view()), name="portal"),
    path('pay', Pay.as_view()),
    path('slot', Slot.as_view()),
    path('commit', Commit.as_view()),
    path('browse', Browse.as_view()),
    path('pause', Pause.as_view()),
    path('gen_rc', GenerateRC.as_view()),
    path('activate', ActivateDevice.as_view()),
    path('sweep', Sweep.as_view()),
    path('voucher', GenerateVoucher.as_view()),
    path('redeem', Redeem.as_view()),
    path('eload', EloadPortal.as_view()),
    path('stream', views.Stream, name='stream'),
]