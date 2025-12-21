# 📚 Sistema de Reservas de Salas

Sistema web para la gestión y reserva de salas de estudio con control de horarios, materiales y usuarios.

## 🚀 Características

- ✅ Reserva de salas con visualización en tiempo real
- ✅ Gestión de bloques horarios configurables por día
- ✅ Sistema de roles (Estudiante, Profesor, Staff, Admin)
- ✅ Materiales adicionales por sala
- ✅ Validaciones de negocio (máx 2h/día, 2 días anticipación)
- ✅ Panel de administración completo
- ✅ Bloqueos de salas por mantenimiento

## 📋 Requisitos Previos

- Python 3.8 o superior
- Django 4.2 o superior

## 🛠️ Instalación

1. **Clonar el repositorio:**
```bash
git clone <URL_DE_TU_REPO>
cd sala_reservas
```

2. **Crear entorno virtual:**
```bash
python -m venv venv
```

3. **Activar entorno virtual:**
   - Windows:
```bash
   venv\Scripts\activate
```
   - Linux/Mac:
```bash
   source venv/bin/activate
```

4. **Instalar dependencias:**
```bash
pip install -r requirements.txt
```

5. **Aplicar migraciones:**
```bash
python manage.py migrate
```

6. **Crear superusuario:**
```bash
python manage.py createsuperuser
```

7. **Crear datos iniciales (roles y bloques):**
```bash
python manage.py crear_roles
python manage.py crear_bloques
```

8. **Ejecutar servidor:**
```bash
python manage.py runserver
```

9. **Acceder:**
   - Frontend: http://127.0.0.1:8000/
   - Admin: http://127.0.0.1:8000/admin/

## 📦 Comandos Útiles

### Crear bloques horarios
```bash
python manage.py crear_bloques
```

### Crear roles del sistema
```bash
python manage.py crear_roles
```

### Cargar usuarios desde CSV
```bash
python manage.py cargar_usuarios usuarios.csv
```

## 🗂️ Estructura del Proyecto
```
sala_reservas/
├── manage.py
├── sala_reservas/         # Configuración del proyecto
│   ├── settings.py
│   ├── urls.py
│   └── ...
├── reservas/              # Aplicación principal
│   ├── models.py          # Modelos de datos
│   ├── views.py           # Vistas
│   ├── admin.py           # Configuración admin
│   ├── urls.py            # URLs
│   ├── templates/         # Templates HTML
│   ├── static/            # Archivos estáticos
│   └── management/        # Comandos personalizados
│       └── commands/
│           ├── crear_bloques.py
│           ├── crear_roles.py
│           └── cargar_usuarios.py
└── requirements.txt
```

## 👥 Roles del Sistema

- **Estudiante**: Puede reservar salas públicas (máx 2h/día)
- **Profesor**: Puede reservar hasta 4h/día
- **Staff**: Acceso a salas internas
- **Admin**: Control total del sistema

## 📝 Configuración

### Reglas de Reserva

Las reglas se configuran desde el admin en "Configuración de Reglas":
- Máximo de horas por día
- Días máximos de anticipación
- Máximo de reservas activas

### Bloques Horarios

Los bloques horarios se definen por día de la semana en el admin.
Ejemplo: Lunes 9:00-11:00, Martes 10:00-12:00, etc.

## 🔧 Configuración para Producción

1. Cambiar `DEBUG = False` en `settings.py`
2. Configurar `ALLOWED_HOSTS`
3. Usar base de datos PostgreSQL
4. Configurar `STATIC_ROOT` y ejecutar `collectstatic`
5. Configurar servidor web (nginx/Apache)

