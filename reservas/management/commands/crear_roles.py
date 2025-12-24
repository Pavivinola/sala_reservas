from django.core.management.base import BaseCommand
from reservas.models import Role


class Command(BaseCommand):
    help = 'Crea los roles básicos del sistema'

    def handle(self, *args, **kwargs):
        roles_data = [
            {
                'name': 'estudiante',
                'display_name': 'Estudiante',
                'description': 'Estudiante regular de la universidad',
                'can_reserve': True,
                'can_reserve_internal_rooms': False,
                'max_hours_override': None,
                'priority': 10,
            },
            {
                'name': 'profesor',
                'display_name': 'Profesor',
                'description': 'Profesor de la universidad con permisos extendidos',
                'can_reserve': True,
                'can_reserve_internal_rooms': False,
                'max_hours_override': 4,
                'priority': 20,
            },
            {
                'name': 'personal',
                'display_name': 'Personal Administrativo',
                'description': 'Personal administrativo con acceso a salas internas',
                'can_reserve': True,
                'can_reserve_internal_rooms': True,
                'max_hours_override': None,
                'priority': 30,
            },
            {
                'name': 'administrador',
                'display_name': 'Administrador',
                'description': 'Administrador del sistema con acceso completo',
                'can_reserve': True,
                'can_reserve_internal_rooms': True,
                'max_hours_override': None,
                'priority': 100,
            },
        ]

        for role_data in roles_data:
            role, created = Role.objects.get_or_create(
                name=role_data['name'],
                defaults=role_data
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Rol creado: {role.display_name}')
                )
            else:
                # Actualizar si ya existe
                for key, value in role_data.items():
                    setattr(role, key, value)
                role.save()
                self.stdout.write(
                    self.style.WARNING(f'↻ Rol actualizado: {role.display_name}')
                )

        self.stdout.write(self.style.SUCCESS('\n🎉 Roles configurados correctamente'))