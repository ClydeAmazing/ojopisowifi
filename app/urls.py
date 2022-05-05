from django.urls import path
from app import views
from app.views import *
# from opw.celery import testing 

app_name = 'app'

urlpatterns = [
    path('portal', Portal.as_view(), name='portal'),
    path('portal/<fas>', Portal.as_view(), name="fas_decode"),
    path('redeem', Redeem.as_view(), name="redeem"),
    # path('pay', Pay.as_view()),
    path('commit', Commit.as_view()),
]