from django.contrib import messages
from django.shortcuts import redirect
from functools import wraps


def user_can_reserve(view_func):
    """
    Decorador que verifica si el usuario tiene permiso para reservar
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # Verificar si tiene perfil
        if not hasattr(request.user, 'profile'):
            messages.error(request, 'Tu cuenta no tiene un perfil asignado. Contacta al administrador.')
            return redirect('reservas:index')
        
        # Verificar si su rol permite reservar
        if not request.user.profile.role.can_reserve:
            messages.error(request, 'Tu rol no tiene permisos para hacer reservas.')
            return redirect('reservas:index')
        
        # Verificar si el perfil está activo
        if not request.user.profile.is_active:
            messages.error(request, 'Tu cuenta está inactiva. Contacta al administrador.')
            return redirect('reservas:index')
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


def staff_required(view_func):
    """
    Decorador que verifica si el usuario es staff/admin
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_staff:
            messages.error(request, 'No tienes permisos para acceder a esta sección.')
            return redirect('reservas:index')
        
        return view_func(request, *args, **kwargs)
    
    return wrapper
