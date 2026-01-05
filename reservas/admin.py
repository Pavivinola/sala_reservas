from django.contrib import admin
from django.utils.html import format_html
from .models import Material, Room, TimeBlock, RoomUnavailability, ReservationRules, Reservation, Role, UserProfile
from django.shortcuts import render, redirect
from django.urls import path
from django.contrib import messages
from django.contrib.auth.models import User
from .forms import BulkUserUploadForm
import openpyxl
from django.contrib.auth.hashers import make_password
import string
import random

# ========================================
# ADMIN: Material
# ========================================
@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'is_active', 'room_count']
    list_filter = ['is_active']
    search_fields = ['name', 'description']
    list_editable = ['is_active']
    
    def room_count(self, obj):
        """Muestra cuántas salas tienen este material"""
        count = obj.rooms.count()
        return f"{count} sala(s)"
    room_count.short_description = "Salas que lo tienen"


# ========================================
# ADMIN: Room
# ========================================
@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ['name', 'capacity', 'location', 'visibility_badge', 'active_badge', 'materials_list']
    list_filter = ['is_public', 'is_active', 'location']
    search_fields = ['name', 'location']
    filter_horizontal = ['available_materials']  # Widget mejor para M2M
    list_editable = ['capacity']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('name', 'capacity', 'location')
        }),
        ('Materiales Disponibles', {
            'fields': ('available_materials',),
            'description': 'Selecciona los materiales que estarán disponibles en esta sala'
        }),
        ('Configuración', {
            'fields': ('is_public', 'is_active'),
            'description': 'Controla la visibilidad y disponibilidad de la sala'
        }),
    )
    
    def visibility_badge(self, obj):
        """Badge visual para visibilidad"""
        if obj.is_public:
            return format_html('<span style="color: green;">✓ Pública</span>')
        return format_html('<span style="color: orange;">⚠ Uso Interno</span>')
    visibility_badge.short_description = "Visibilidad"
    
    def active_badge(self, obj):
        """Badge visual para estado activo"""
        if obj.is_active:
            return format_html('<span style="color: green;">✓ Activa</span>')
        return format_html('<span style="color: red;">✗ Inactiva</span>')
    active_badge.short_description = "Estado"
    
    def materials_list(self, obj):
        """Lista los materiales de la sala"""
        materials = obj.available_materials.filter(is_active=True)
        if materials.exists():
            return ", ".join([m.name for m in materials])
        return "Sin materiales"
    materials_list.short_description = "Materiales"


# ========================================
# ADMIN: TimeBlock
# ========================================
@admin.register(TimeBlock)
class TimeBlockAdmin(admin.ModelAdmin):
    list_display = ['day_badge', 'name', 'start_time', 'end_time', 'duration_display', 'is_active']
    list_filter = ['day_of_week', 'is_active']
    search_fields = ['name']
    list_editable = ['is_active']
    ordering = ['day_of_week', 'start_time']
    
    fieldsets = (
        ('Información del Bloque', {
            'fields': ('name', 'day_of_week')
        }),
        ('Horario', {
            'fields': ('start_time', 'end_time'),
            'description': 'Define el rango de horario para este bloque'
        }),
        ('Estado', {
            'fields': ('is_active',)
        }),
    )
    
    def day_badge(self, obj):
        """Badge visual para el día"""
        day_colors = {
            'monday': '#3498db',
            'tuesday': '#3498db',
            'wednesday': '#3498db',
            'thursday': '#3498db',
            'friday': '#3498db',
            'saturday': '#e74c3c',
            'sunday': '#95a5a6',
        }
        color = day_colors.get(obj.day_of_week, '#95a5a6')
        day_name = obj.get_day_of_week_display()
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            day_name
        )
    day_badge.short_description = "Día"
    
    def duration_display(self, obj):
        """Muestra la duración del bloque"""
        hours = obj.duration_hours()
        return f"{hours} hora(s)"
    duration_display.short_description = "Duración"
# ========================================
# ADMIN: RoomUnavailability
# ========================================
@admin.register(RoomUnavailability)
class RoomUnavailabilityAdmin(admin.ModelAdmin):
    list_display = ['room', 'date', 'time_block', 'reason', 'created_at']
    list_filter = ['room', 'date']
    search_fields = ['room__name', 'reason']
    date_hierarchy = 'date'
    autocomplete_fields = ['room']  # Búsqueda rápida de salas
    
    fieldsets = (
        ('Bloqueo', {
            'fields': ('room', 'date', 'time_block'),
        }),
        ('Detalles', {
            'fields': ('reason',),
        }),
    )


# ========================================
# ADMIN: ReservationRules (Singleton)
# ========================================
@admin.register(ReservationRules)
class ReservationRulesAdmin(admin.ModelAdmin):
    list_display = ['max_hours_per_day', 'max_days_in_advance', 'max_active_reservations', 'updated_at', 'updated_by']
    
    fieldsets = (
        ('Reglas de Reserva', {
            'fields': ('max_hours_per_day', 'max_days_in_advance', 'max_active_reservations'),
            'description': 'Estas reglas aplican a todos los usuarios del sistema'
        }),
    )
    
    def has_add_permission(self, request):
        """Solo permitir crear si no existe una instancia"""
        if ReservationRules.objects.exists():
            return False
        return True
    
    def has_delete_permission(self, request, obj=None):
        """No permitir eliminar las reglas"""
        return False
    
    def save_model(self, request, obj, form, change):
        """Guardar quién modificó las reglas"""
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


# ========================================
# ADMIN: Reservation
# ========================================
class RequestedMaterialsInline(admin.TabularInline):
    """Inline para mostrar materiales solicitados"""
    model = Reservation.requested_materials.through
    extra = 0
    verbose_name = "Material Solicitado"
    verbose_name_plural = "Materiales Solicitados"


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ['user', 'room', 'date', 'time_block', 'status_badge', 'materials_requested', 'created_at']
    list_filter = ['status', 'date', 'room', 'time_block']
    search_fields = ['user__username', 'user__email', 'room__name']
    date_hierarchy = 'date'
    filter_horizontal = ['requested_materials']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Reserva', {
            'fields': ('user', 'room', 'date', 'time_block')
        }),
        ('Materiales', {
            'fields': ('requested_materials',),
            'description': 'Solo se pueden solicitar materiales disponibles en la sala seleccionada'
        }),
        ('Estado y Notas', {
            'fields': ('status', 'notes')
        }),
        ('Información del Sistema', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def status_badge(self, obj):
        """Badge colorido para el estado"""
        colors = {
            'pending': 'orange',
            'confirmed': 'green',
            'cancelled': 'red',
            'completed': 'blue'
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">● {}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = "Estado"
    
    def materials_requested(self, obj):
        """Lista de materiales solicitados"""
        materials = obj.requested_materials.all()
        if materials.exists():
            return ", ".join([m.name for m in materials])
        return "Sin materiales"
    materials_requested.short_description = "Materiales"
    
    def get_form(self, request, obj=None, **kwargs):
        """Filtrar materiales disponibles según la sala seleccionada"""
        form = super().get_form(request, obj, **kwargs)
        if obj and obj.room:
            # Limitar materiales a los disponibles en la sala
            form.base_fields['requested_materials'].queryset = obj.room.available_materials.filter(is_active=True)
        return form


# ========================================
# Personalización del Admin Site
# ========================================
admin.site.site_header = "Sistema de Reservas de Salas"
admin.site.site_title = "Admin Reservas"
admin.site.index_title = "Panel de Administración"

# ========================================
# ADMIN: Role
# ========================================
@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = [
        'display_name', 
        'name',
        'can_reserve_badge', 
        'internal_rooms_badge',
        'max_hours_display',
        'priority',
        'user_count'
    ]
    list_filter = ['can_reserve', 'can_reserve_internal_rooms']
    search_fields = ['name', 'display_name', 'description']
    list_editable = ['priority']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('name', 'display_name', 'description'),
            'description': 'Define el nombre técnico y el nombre visible del rol'
        }),
        ('Permisos de Reserva', {
            'fields': ('can_reserve', 'can_reserve_internal_rooms', 'max_hours_override'),
            'description': 'Configura qué puede hacer este rol en el sistema'
        }),
        ('Configuración Avanzada', {
            'fields': ('priority',),
            'description': 'Mayor número = mayor prioridad',
            'classes': ('collapse',)
        }),
    )
    
    def can_reserve_badge(self, obj):
        """Badge para permiso de reserva"""
        if obj.can_reserve:
            return format_html('<span style="color: green; font-weight: bold;">✓ Sí</span>')
        return format_html('<span style="color: red;">✗ No</span>')
    can_reserve_badge.short_description = "Puede Reservar"
    
    def internal_rooms_badge(self, obj):
        """Badge para salas internas"""
        if obj.can_reserve_internal_rooms:
            return format_html('<span style="color: orange; font-weight: bold;">✓ Sí</span>')
        return format_html('<span style="color: gray;">✗ No</span>')
    internal_rooms_badge.short_description = "Salas Internas"
    
    def max_hours_display(self, obj):
        """Muestra las horas máximas"""
        if obj.max_hours_override:
            return f"{obj.max_hours_override}h/día"
        return "Regla global"
    max_hours_display.short_description = "Máx. Horas"
    
    def user_count(self, obj):
        """Cantidad de usuarios con este rol"""
        count = obj.users.count()
        return format_html(
            '<span style="background: #667eea; color: white; padding: 2px 8px; border-radius: 10px;">{}</span>',
            count
        )
    user_count.short_description = "Usuarios"
# ========================================
# ADMIN: UserProfile con Carga Masiva
# ========================================
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'department', 'alma_user_id', 'is_active']
    list_filter = ['role', 'is_active']
    search_fields = ['user__username', 'user__email', 'alma_user_id', 'department']
    autocomplete_fields = ['user']
    
    fieldsets = (
        ('Usuario Django', {
            'fields': ('user',)
        }),
        ('Información de Rol', {
            'fields': ('role', 'department')
        }),
        ('Integración Alma', {
            'fields': ('alma_user_id',),
            'classes': ('collapse',)
        }),
        ('Contacto', {
            'fields': ('phone',)
        }),
        ('Estado', {
            'fields': ('is_active',)
        }),
    )
    
    # Agregar URLs personalizadas
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('bulk-upload/', self.admin_site.admin_view(self.bulk_upload_view), name='reservas_userprofile_bulk_upload'),
        ]
        return custom_urls + urls
    
    # Vista de carga masiva
    def bulk_upload_view(self, request):
        if request.method == 'POST':
            form = BulkUserUploadForm(request.POST, request.FILES)
            if form.is_valid():
                excel_file = request.FILES['excel_file']
                send_email = form.cleaned_data['send_welcome_email']
                
                # Procesar el archivo Excel
                result = self.process_excel_file(excel_file, send_email)
                
                # Mostrar resultados
                if result['created'] > 0:
                    messages.success(request, f"✓ {result['created']} usuario(s) creado(s) exitosamente")
                
                if result['errors']:
                    for error in result['errors']:
                        messages.error(request, f"✗ {error}")
                
                return redirect('..')
        else:
            form = BulkUserUploadForm()
        
        context = {
            'form': form,
            'title': 'Carga Masiva de Usuarios',
            'site_header': 'Sistema de Reservas',
        }
        return render(request, 'admin/reservas/userprofile/bulk_upload.html', context)
    
    # Procesar archivo Excel
    def process_excel_file(self, excel_file, send_email):
        result = {'created': 0, 'errors': []}
        
        try:
            workbook = openpyxl.load_workbook(excel_file)
            sheet = workbook.active
            
            # Leer encabezados (primera fila)
            headers = [cell.value for cell in sheet[1]]
            
            # Validar que tenga las columnas necesarias
            required_columns = ['username', 'email', 'first_name', 'last_name', 'role_name']
            for col in required_columns:
                if col not in headers:
                    result['errors'].append(f"Falta columna requerida: {col}")
                    return result
            
            # Procesar cada fila (desde la 2 en adelante)
            for row_num, row in enumerate(sheet.iter_rows(min_row=2, values_only=True), start=2):
                try:
                    # Convertir fila a diccionario
                    row_data = dict(zip(headers, row))
                    
                    # Saltar filas vacías
                    if not row_data.get('username'):
                        continue
                    
                    # Verificar si el usuario ya existe
                    if User.objects.filter(username=row_data['username']).exists():
                        result['errors'].append(f"Fila {row_num}: Usuario '{row_data['username']}' ya existe")
                        continue
                    
                    # Buscar el rol
                    try:
                        role = Role.objects.get(name=row_data['role_name'])
                    except Role.DoesNotExist:
                        result['errors'].append(f"Fila {row_num}: Rol '{row_data['role_name']}' no existe")
                        continue
                    
                    # Generar contraseña si no viene en el Excel
                    password = row_data.get('password')
                    if not password:
                        password = self.generate_random_password()
                    
                    # Crear usuario de Django
                    user = User.objects.create(
                        username=row_data['username'],
                        email=row_data['email'],
                        first_name=row_data.get('first_name', ''),
                        last_name=row_data.get('last_name', ''),
                        is_staff=row_data.get('is_staff', 'FALSE').upper() == 'TRUE',
                        password=make_password(password)
                    )
                    
                    # Crear perfil
                    UserProfile.objects.create(
                        user=user,
                        role=role,
                        department=row_data.get('department', ''),
                        phone=row_data.get('phone', ''),
                        alma_user_id=row_data.get('alma_user_id', ''),
                        is_active=True
                    )
                    
                    result['created'] += 1
                    
                    # TODO: Enviar email si send_email es True
                    # Aquí puedes agregar lógica de envío de email con las credenciales
                    
                except Exception as e:
                    result['errors'].append(f"Fila {row_num}: {str(e)}")
            
        except Exception as e:
            result['errors'].append(f"Error al leer el archivo: {str(e)}")
        
        return result
    
    # Generar contraseña aleatoria
    def generate_random_password(self, length=10):
        characters = string.ascii_letters + string.digits
        return ''.join(random.choice(characters) for i in range(length))
    
    # Agregar botón en el listado
    change_list_template = 'admin/reservas/userprofile/change_list.html'