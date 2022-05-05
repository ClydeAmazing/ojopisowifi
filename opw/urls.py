from django.contrib import admin
from django.urls import path, include
from django.views.generic.base import RedirectView

from django.conf.urls.static import static
from django.conf import settings

from app.admin import ojo_admin

from .views import Main

urlpatterns = [
    path('app/', include('app.urls')),
    # path('app/admin/', admin.site.urls),
    path('app/admin/', ojo_admin.urls),
    path('app/api/', include('app.api.urls')),
    path('', Main.as_view(), name='index')
    # path('', RedirectView.as_view(url='/app/portal')),
] 
