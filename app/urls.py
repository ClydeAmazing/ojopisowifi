from django.urls import path
from app.views import Portal, Redeem, Commit

app_name = 'app'

urlpatterns = [
    path('portal', Portal.as_view(), name='portal'),
    path('redeem', Redeem.as_view(), name="redeem"),
    path('commit', Commit.as_view()),
]