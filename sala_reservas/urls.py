from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from django.contrib.auth import views as auth_views
from reservas import views as reservas_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('reservas/', include('reservas.urls')),
    
    # Login/Logout para usuarios normales
    path('login/', auth_views.LoginView.as_view(template_name='reservas/login.html'), name='login'),
    path('logout/', reservas_views.logout_view, name='logout'),
    #path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    #path('logout/', auth_views.LogoutView.as_view(next_page='login', http_method_names=['get', 'post']), name='logout'),
    
    # Redirigir raíz a reservas
    path('', lambda request: redirect('reservas:index')),
]