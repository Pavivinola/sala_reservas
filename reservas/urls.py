from django.urls import path
from . import views

app_name = 'reservas'

urlpatterns = [
    path('', views.index, name='index'),
    path('disponibilidad/', views.disponibilidad, name='disponibilidad'),
    path('reservar/<int:room_id>/<int:timeblock_id>/<str:date>/', views.reservar, name='reservar'),
    path('mis-reservas/', views.mis_reservas, name='mis_reservas'),
    path('cancelar/<int:reservation_id>/', views.cancelar_reserva, name='cancelar_reserva'),
]