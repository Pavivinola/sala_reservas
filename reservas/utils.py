def user_can_access_room(user, room):
    """
    Verifica si un usuario puede acceder/reservar una sala específica
    """
    # Si la sala es pública, cualquiera puede acceder
    if room.is_public:
        return True
    
    # Si la sala es interna, verificar permiso especial
    if hasattr(user, 'profile'):
        return user.profile.role.can_reserve_internal_rooms
    
    return False


def get_available_rooms_for_user(user):
    """
    Retorna las salas que un usuario puede ver/reservar
    """
    from .models import Room
    
    # Si no tiene perfil, solo salas públicas
    if not hasattr(user, 'profile'):
        return Room.objects.filter(is_public=True, is_active=True)
    
    # Si puede acceder a salas internas, mostrar todas
    if user.profile.role.can_reserve_internal_rooms:
        return Room.objects.filter(is_active=True)
    
    # Si no, solo públicas
    return Room.objects.filter(is_public=True, is_active=True)
