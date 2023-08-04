from django.urls import path
from rest_framework.authtoken.views import obtain_auth_token
from app.api.views import DashboardDetails, CreateUser

urlpatterns = [
	path('dashboard_data/', DashboardDetails.as_view()),
    path('create_user/', CreateUser.as_view(), name='create_user'),
    path('obtain_api_token/', obtain_auth_token)
]