from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect

urlpatterns = [
    path('admin/', admin.site.urls),
    path('reservas/', include('reservas.urls')),
    path('', lambda request: redirect('reservas:index')),  # Redirigir raíz a reservas
]