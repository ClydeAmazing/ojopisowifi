from django.urls import path
from rest_framework.authtoken.views import obtain_auth_token
from app.api.views import DashboardDetails, CreateUser, GetUser

urlpatterns = [
	path('dashboard_data/', DashboardDetails.as_view()),
    path('create_user/', CreateUser.as_view(), name='create_user'),
    path('user/<str:client_mac>/', GetUser.as_view(http_method_names=['get']), name='get_user'),
    path('user/<str:client_mac>/<str:action>/', GetUser.as_view(http_method_names=['post']), name='update_user'),
    path('obtain_api_token/', obtain_auth_token)
]