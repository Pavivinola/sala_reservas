from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from datetime import datetime, timedelta, date
from django.db.models import Q
from .models import Room, TimeBlock, Reservation, ReservationRules, RoomUnavailability


def index(request):
    """Página principal"""
    context = {
        'total_salas': Room.objects.filter(is_active=True, is_public=True).count(),
        'total_bloques': TimeBlock.objects.filter(is_active=True).count(),
    }
    return render(request, 'reservas/index.html', context)


def disponibilidad(request):
    """Grid de disponibilidad de salas"""
    # Obtener fecha del parámetro GET o usar hoy
    fecha_str = request.GET.get('fecha', date.today().isoformat())
    try:
        fecha_seleccionada = datetime.strptime(fecha_str, '%Y-%m-%d').date()
    except ValueError:
        fecha_seleccionada = date.today()
    
    # Validar que no sea fecha pasada
    if fecha_seleccionada < date.today():
        fecha_seleccionada = date.today()
    
    # Obtener reglas
    reglas = ReservationRules.objects.first()
    max_dias_anticipacion = reglas.max_days_in_advance if reglas else 2
    
    # Validar límite de anticipación
    fecha_maxima = date.today() + timedelta(days=max_dias_anticipacion)
    if fecha_seleccionada > fecha_maxima:
        fecha_seleccionada = fecha_maxima
    
    # Obtener día de la semana en inglés
    dias_semana = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
    dia_semana = dias_semana[fecha_seleccionada.weekday()]
    
    # Obtener salas públicas y activas
    salas = Room.objects.filter(is_public=True, is_active=True).order_by('name')
    
    # Obtener bloques horarios para ese día
    bloques = TimeBlock.objects.filter(
        day_of_week=dia_semana,
        is_active=True
    ).order_by('start_time')
    
    # Construir matriz de disponibilidad
    disponibilidad_grid = []
    
    for sala in salas:
        fila = {
            'sala': sala,
            'bloques': []
        }
        
        for bloque in bloques:
            # Verificar si hay reserva
            reserva = Reservation.objects.filter(
                room=sala,
                date=fecha_seleccionada,
                time_block=bloque,
                status__in=['pending', 'confirmed']
            ).first()
            
            # Verificar si está bloqueada
            bloqueada = RoomUnavailability.objects.filter(
                Q(room=sala, date=fecha_seleccionada, time_block=bloque) |
                Q(room=sala, date=fecha_seleccionada, time_block__isnull=True)  # Bloqueada todo el día
            ).exists()
            
            # Determinar estado
            if bloqueada:
                estado = 'bloqueado'
            elif reserva:
                estado = 'reservado'
            else:
                estado = 'disponible'
            
            fila['bloques'].append({
                'bloque': bloque,
                'estado': estado,
                'reserva': reserva
            })
        
        disponibilidad_grid.append(fila)
    
    # Fechas para navegación
    fecha_anterior = fecha_seleccionada - timedelta(days=1)
    fecha_siguiente = fecha_seleccionada + timedelta(days=1)
    
    # No permitir ir al pasado
    if fecha_anterior < date.today():
        fecha_anterior = None
    
    # No permitir exceder máximo de anticipación
    if fecha_siguiente > fecha_maxima:
        fecha_siguiente = None
    
    context = {
        'fecha_seleccionada': fecha_seleccionada,
        'fecha_anterior': fecha_anterior,
        'fecha_siguiente': fecha_siguiente,
        'bloques': bloques,
        'disponibilidad_grid': disponibilidad_grid,
        'max_dias_anticipacion': max_dias_anticipacion,
    }
    
    return render(request, 'reservas/disponibilidad.html', context)


@login_required
def reservar(request, room_id, timeblock_id, date):
    """Procesar reserva de sala"""
    sala = get_object_or_404(Room, pk=room_id, is_active=True)
    bloque = get_object_or_404(TimeBlock, pk=timeblock_id, is_active=True)
    
    try:
        fecha = datetime.strptime(date, '%Y-%m-%d').date()
    except ValueError:
        messages.error(request, 'Fecha inválida')
        return redirect('reservas:disponibilidad')
    
    # Validaciones
    reglas = ReservationRules.objects.first()
    
    # 1. Verificar que no sea fecha pasada
    if fecha < timezone.now().date():
        messages.error(request, 'No puedes reservar en fechas pasadas')
        return redirect('reservas:disponibilidad')
    
    # 2. Verificar límite de anticipación
    max_dias = reglas.max_days_in_advance if reglas else 2
    if fecha > timezone.now().date() + timedelta(days=max_dias):
        messages.error(request, f'No puedes reservar con más de {max_dias} días de anticipación')
        return redirect('reservas:disponibilidad')
    
    # 3. Verificar que no esté ya reservada
    if Reservation.objects.filter(
        room=sala,
        date=fecha,
        time_block=bloque,
        status__in=['pending', 'confirmed']
    ).exists():
        messages.error(request, 'Este horario ya está reservado')
        return redirect('reservas:disponibilidad')
    
    # 4. Verificar que no esté bloqueada
    if RoomUnavailability.objects.filter(
        Q(room=sala, date=fecha, time_block=bloque) |
        Q(room=sala, date=fecha, time_block__isnull=True)
    ).exists():
        messages.error(request, 'Este horario no está disponible')
        return redirect('reservas:disponibilidad')
    
    # 5. Verificar límite de horas por día del usuario
    max_horas = reglas.max_hours_per_day if reglas else 2
    if hasattr(request.user, 'profile'):
        max_horas = request.user.profile.get_max_hours_per_day()
    
    # Calcular horas ya reservadas ese día
    reservas_dia = Reservation.objects.filter(
        user=request.user,
        date=fecha,
        status__in=['pending', 'confirmed']
    )
    
    horas_reservadas = sum([r.time_block.duration_hours() for r in reservas_dia])
    horas_nueva_reserva = bloque.duration_hours()
    
    if horas_reservadas + horas_nueva_reserva > max_horas:
        messages.error(
            request,
            f'No puedes reservar más de {max_horas} horas por día. '
            f'Ya tienes {horas_reservadas} horas reservadas.'
        )
        return redirect('reservas:disponibilidad')
    
    # Si es POST, procesar formulario de materiales
    if request.method == 'POST':
        materiales_ids = request.POST.getlist('materiales')
        
        # Crear reserva
        reserva = Reservation.objects.create(
            user=request.user,
            room=sala,
            date=fecha,
            time_block=bloque,
            status='confirmed',
            notes=request.POST.get('notas', '')
        )
        
        # Agregar materiales solicitados
        if materiales_ids:
            reserva.requested_materials.set(materiales_ids)
        
        messages.success(
            request,
            f'¡Reserva confirmada! {sala.name} el {fecha.strftime("%d/%m/%Y")} '
            f'de {bloque.start_time.strftime("%H:%M")} a {bloque.end_time.strftime("%H:%M")}'
        )
        return redirect('reservas:mis_reservas')
    
    # Mostrar formulario de confirmación
    context = {
        'sala': sala,
        'bloque': bloque,
        'fecha': fecha,
        'materiales_disponibles': sala.available_materials.filter(is_active=True),
    }
    return render(request, 'reservas/confirmar.html', context)


@login_required
def mis_reservas(request):
    """Ver reservas del usuario"""
    reservas_activas = Reservation.objects.filter(
        user=request.user,
        status__in=['pending', 'confirmed'],
        date__gte=timezone.now().date()
    ).select_related('room', 'time_block').order_by('date', 'time_block__start_time')
    
    reservas_pasadas = Reservation.objects.filter(
        user=request.user,
        date__lt=timezone.now().date()
    ).select_related('room', 'time_block').order_by('-date', '-time_block__start_time')[:10]
    
    context = {
        'reservas_activas': reservas_activas,
        'reservas_pasadas': reservas_pasadas,
    }
    return render(request, 'reservas/mis_reservas.html', context)


@login_required
def cancelar_reserva(request, reservation_id):
    """Cancelar una reserva"""
    reserva = get_object_or_404(Reservation, pk=reservation_id, user=request.user)
    
    # Solo permitir cancelar si es futura y no está ya cancelada
    if reserva.date < timezone.now().date():
        messages.error(request, 'No puedes cancelar una reserva pasada')
    elif reserva.status == 'cancelled':
        messages.warning(request, 'Esta reserva ya está cancelada')
    else:
        reserva.status = 'cancelled'
        reserva.save()
        messages.success(request, 'Reserva cancelada exitosamente')
    
    return redirect('reservas:mis_reservas')