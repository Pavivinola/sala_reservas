from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta


# ========================================
# MODELO: Material
# ========================================
# Catálogo de materiales que pueden estar disponibles en las salas
class Material(models.Model):
    name = models.CharField(max_length=100, verbose_name="Nombre")
    description = models.TextField(blank=True, verbose_name="Descripción")
    is_active = models.BooleanField(default=True, verbose_name="Activo")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Material"
        verbose_name_plural = "Materiales"
        ordering = ['name']

    def __str__(self):
        return self.name


# ========================================
# MODELO: Room (Sala)
# ========================================
class Room(models.Model):
    name = models.CharField(max_length=100, verbose_name="Nombre de la sala")
    capacity = models.PositiveIntegerField(verbose_name="Capacidad (personas)")
    location = models.CharField(max_length=200, verbose_name="Ubicación")
    
    # Materiales disponibles en esta sala
    available_materials = models.ManyToManyField(
        Material,
        blank=True,
        verbose_name="Materiales disponibles",
        related_name="rooms"
    )
    
    # Control de visibilidad
    is_public = models.BooleanField(
        default=True,
        verbose_name="Sala pública",
        help_text="Si está desmarcado, solo el admin puede reservar esta sala"
    )
    
    is_active = models.BooleanField(default=True, verbose_name="Activa")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Sala"
        verbose_name_plural = "Salas"
        ordering = ['name']

    def __str__(self):
        status = "Pública" if self.is_public else "Uso Interno"
        return f"{self.name} - Cap: {self.capacity} ({status})"


# ========================================
# MODELO: TimeBlock (Bloque Horario)
# ========================================
# ========================================
# MODELO: TimeBlock (Bloque Horario)
# ========================================
class TimeBlock(models.Model):
    DAYS_OF_WEEK = [
        ('monday', 'Lunes'),
        ('tuesday', 'Martes'),
        ('wednesday', 'Miércoles'),
        ('thursday', 'Jueves'),
        ('friday', 'Viernes'),
        ('saturday', 'Sábado'),
        ('sunday', 'Domingo'),
    ]
    
    name = models.CharField(
        max_length=50,
        verbose_name="Nombre del bloque",
        help_text="Ej: Bloque 1, Bloque Mañana, Sábado Tarde"
    )
    day_of_week = models.CharField(
        max_length=10,
        choices=DAYS_OF_WEEK,
        verbose_name="Día de la semana",
        help_text="Día al que aplica este bloque horario"
    )
    start_time = models.TimeField(verbose_name="Hora inicio")
    end_time = models.TimeField(verbose_name="Hora fin")
    is_active = models.BooleanField(default=True, verbose_name="Activo")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Bloque Horario"
        verbose_name_plural = "Bloques Horarios"
        ordering = ['day_of_week', 'start_time']
        unique_together = ['day_of_week', 'start_time', 'end_time']
        # Evita bloques duplicados para el mismo día/horario

    def __str__(self):
        day_name = dict(self.DAYS_OF_WEEK).get(self.day_of_week, self.day_of_week)
        return f"{day_name} - {self.name} ({self.start_time.strftime('%H:%M')} - {self.end_time.strftime('%H:%M')})"

    def clean(self):
        # Validar que hora fin sea mayor que hora inicio
        if self.start_time >= self.end_time:
            raise ValidationError("La hora de fin debe ser posterior a la hora de inicio")

    def duration_hours(self):
        """Retorna la duración del bloque en horas"""
        from datetime import datetime
        start = datetime.combine(datetime.today(), self.start_time)
        end = datetime.combine(datetime.today(), self.end_time)
        duration = end - start
        return duration.total_seconds() / 3600
    
    def get_day_display_short(self):
        """Retorna abreviatura del día"""
        abbreviations = {
            'monday': 'Lun',
            'tuesday': 'Mar',
            'wednesday': 'Mié',
            'thursday': 'Jue',
            'friday': 'Vie',
            'saturday': 'Sáb',
            'sunday': 'Dom',
        }
        return abbreviations.get(self.day_of_week, self.day_of_week)


# ========================================
# MODELO: RoomUnavailability (Bloqueos)
# ========================================
class RoomUnavailability(models.Model):
    room = models.ForeignKey(
        Room,
        on_delete=models.CASCADE,
        verbose_name="Sala",
        related_name="unavailabilities"
    )
    date = models.DateField(verbose_name="Fecha")
    time_block = models.ForeignKey(
        TimeBlock,
        on_delete=models.CASCADE,
        verbose_name="Bloque horario",
        null=True,
        blank=True,
        help_text="Dejar vacío para bloquear todo el día"
    )
    reason = models.CharField(
        max_length=200,
        verbose_name="Motivo",
        help_text="Ej: Mantenimiento, Evento especial"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Bloqueo de Sala"
        verbose_name_plural = "Bloqueos de Salas"
        ordering = ['-date', 'room']
        unique_together = ['room', 'date', 'time_block']

    def __str__(self):
        block_info = f" - {self.time_block}" if self.time_block else " (Todo el día)"
        return f"{self.room.name} - {self.date}{block_info}"


# ========================================
# MODELO: ReservationRules (Reglas Globales)
# ========================================
class ReservationRules(models.Model):
    max_hours_per_day = models.PositiveIntegerField(
        default=2,
        verbose_name="Máximo de horas por día",
        help_text="Horas máximas que un usuario puede reservar por día"
    )
    max_days_in_advance = models.PositiveIntegerField(
        default=2,
        verbose_name="Días máximos de anticipación",
        help_text="Cuántos días hacia el futuro se puede reservar"
    )
    max_active_reservations = models.PositiveIntegerField(
        default=5,
        verbose_name="Máximo de reservas activas",
        help_text="Cantidad máxima de reservas activas simultáneas por usuario"
    )
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Actualizado por"
    )

    class Meta:
        verbose_name = "Configuración de Reglas"
        verbose_name_plural = "Configuración de Reglas"

    def __str__(self):
        return f"Reglas: {self.max_hours_per_day}h/día, {self.max_days_in_advance} días anticipación"

    def save(self, *args, **kwargs):
        # Solo permitir una instancia de reglas
        if not self.pk and ReservationRules.objects.exists():
            raise ValidationError('Solo puede existir una configuración de reglas')
        return super().save(*args, **kwargs)

# ========================================
# MODELO: Role (Rol de Usuario)
# ========================================
class Role(models.Model):
    ROLE_TYPES = [
        ('student', 'Estudiante'),
        ('teacher', 'Profesor'),
        ('staff', 'Personal'),
        ('admin', 'Administrador'),
    ]
    
    name = models.CharField(
        max_length=50,
        choices=ROLE_TYPES,
        unique=True,
        verbose_name="Tipo de rol"
    )
    description = models.TextField(blank=True, verbose_name="Descripción")
    
    # Permisos específicos
    can_reserve = models.BooleanField(default=True, verbose_name="Puede reservar")
    can_reserve_internal_rooms = models.BooleanField(
        default=False,
        verbose_name="Puede reservar salas internas"
    )
    max_hours_override = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Horas máximas (sobrescribe regla global)",
        help_text="Dejar vacío para usar la regla global"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Rol"
        verbose_name_plural = "Roles"

    def __str__(self):
        return self.get_name_display()


# ========================================
# MODELO: UserProfile (Perfil de Usuario)
# ========================================
class UserProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name="Usuario"
    )
    role = models.ForeignKey(
        Role,
        on_delete=models.PROTECT,
        verbose_name="Rol",
        related_name="users"
    )
    
    # Datos de Alma (cuando integremos)
    alma_user_id = models.CharField(
        max_length=100,
        blank=True,
        unique=True,
        null=True,
        verbose_name="ID de Alma"
    )
    
    # Información adicional
    department = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Facultad/Carrera"
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="Teléfono"
    )
    
    is_active = models.BooleanField(default=True, verbose_name="Activo")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Perfil de Usuario"
        verbose_name_plural = "Perfiles de Usuarios"

    def __str__(self):
        return f"{self.user.username} - {self.role}"
    
    def get_max_hours_per_day(self):
        """Retorna las horas máximas según rol o regla global"""
        if self.role.max_hours_override:
            return self.role.max_hours_override
        
        rules = ReservationRules.objects.first()
        return rules.max_hours_per_day if rules else 2
# ========================================
# MODELO: Reservation (Reserva)
# ========================================
class Reservation(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('confirmed', 'Confirmada'),
        ('cancelled', 'Cancelada'),
        ('completed', 'Completada'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="Usuario",
        related_name="reservations"
    )
    room = models.ForeignKey(
        Room,
        on_delete=models.CASCADE,
        verbose_name="Sala",
        related_name="reservations"
    )
    date = models.DateField(verbose_name="Fecha")
    time_block = models.ForeignKey(
        TimeBlock,
        on_delete=models.CASCADE,
        verbose_name="Bloque horario"
    )
    
    # Materiales solicitados (subset de room.available_materials)
    requested_materials = models.ManyToManyField(
        Material,
        blank=True,
        verbose_name="Materiales solicitados",
        related_name="reservations"
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='confirmed',
        verbose_name="Estado"
    )
    
    notes = models.TextField(
        blank=True,
        verbose_name="Notas adicionales"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Reserva"
        verbose_name_plural = "Reservas"
        ordering = ['-date', 'time_block']
        unique_together = ['room', 'date', 'time_block', 'status']
        # Evitar reservas duplicadas activas para la misma sala/fecha/bloque

    def __str__(self):
        return f"{self.user.username} - {self.room.name} - {self.date} ({self.time_block})"

    def clean(self):
        """Validaciones de negocio"""
        if not self.pk:  # Solo validar en creación
            # Validar que la sala esté activa
            if not self.room.is_active:
                raise ValidationError("No se puede reservar una sala inactiva")
            
            # Validar que el bloque horario esté activo
            if not self.time_block.is_active:
                raise ValidationError("No se puede reservar en un bloque horario inactivo")

    def is_past(self):
        """Verifica si la reserva es del pasado"""
        from datetime import datetime
        reservation_datetime = datetime.combine(self.date, self.time_block.start_time)
        return reservation_datetime < timezone.now()