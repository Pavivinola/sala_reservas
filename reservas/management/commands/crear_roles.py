from django.core.management.base import BaseCommand
from reservas.models import Role


class Command(BaseCommand):
    help = 'Crea los roles básicos del sistema'

    def handle(self, *args, **kwargs):
        roles_data = [
            {
                'name': 'student',
                'description': 'Estudiante pregrado',
                'can_reserve': True,
                'can_reserve_internal_rooms': False,
                'max_hours_override': None,
            },
            {
                'name': 'teacher',
                'description': 'Profesor',
                'can_reserve': True,
                'can_reserve_internal_rooms': False,
                'max_hours_override': 4,  # Profesores pueden reservar 4h
            },
            {
                'name': 'staff',
                'description': 'Personal administrativo',
                'can_reserve': True,
                'can_reserve_internal_rooms': True,
                'max_hours_override': None,
            },
            {
                'name': 'admin',
                'description': 'Administrador del sistema',
                'can_reserve': True,
                'can_reserve_internal_rooms': True,
                'max_hours_override': None,
            },
        ]

        for role_data in roles_data:
            role, created = Role.objects.get_or_create(
                name=role_data['name'],
                defaults=role_data
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Rol creado: {role.get_name_display()}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'↻ Rol ya existe: {role.get_name_display()}')
                )

        self.stdout.write(self.style.SUCCESS('\n🎉 Roles configurados correctamente'))