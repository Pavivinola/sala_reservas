import csv
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from reservas.models import Role, UserProfile


class Command(BaseCommand):
    help = 'Carga usuarios masivamente desde un archivo CSV'

    def add_arguments(self, parser):
        parser.add_argument(
            'csv_file',
            type=str,
            help='Ruta al archivo CSV con los usuarios'
        )

    def handle(self, *args, **kwargs):
        csv_file = kwargs['csv_file']
        
        usuarios_creados = 0
        usuarios_actualizados = 0
        errores = 0

        try:
            with open(csv_file, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                
                # Verificar columnas requeridas
                required_columns = ['username', 'email', 'first_name', 'last_name', 'role', 'department']
                if not all(col in reader.fieldnames for col in required_columns):
                    self.stdout.write(
                        self.style.ERROR(
                            f'El CSV debe tener las columnas: {", ".join(required_columns)}'
                        )
                    )
                    return

                for row in reader:
                    try:
                        # Obtener o crear usuario
                        user, created = User.objects.get_or_create(
                            username=row['username'],
                            defaults={
                                'email': row['email'],
                                'first_name': row['first_name'],
                                'last_name': row['last_name'],
                            }
                        )
                        
                        if not created:
                            # Actualizar datos si ya existe
                            user.email = row['email']
                            user.first_name = row['first_name']
                            user.last_name = row['last_name']
                            user.save()
                            usuarios_actualizados += 1
                        else:
                            # Establecer contraseña por defecto para nuevos usuarios
                            user.set_password(row.get('password', 'cambiar123'))
                            user.save()
                            usuarios_creados += 1
                                                
                        # Obtener rol (buscar por name o display_name)
                        try:
                            role = Role.objects.get(name=row['role'])
                        except Role.DoesNotExist:
                            try:
                                role = Role.objects.get(display_name=row['role'])
                            except Role.DoesNotExist:
                                self.stdout.write(
                                    self.style.ERROR(
                                        f'✗ Rol "{row["role"]}" no existe para usuario {row["username"]}'
                                    )
                                )
                                errores += 1
                                continue
                        
                        # Crear o actualizar perfil
                        profile, profile_created = UserProfile.objects.get_or_create(
                            user=user,
                            defaults={
                                'role': role,
                                'department': row.get('department', ''),
                                'alma_user_id': row.get('alma_id', ''),
                                'phone': row.get('phone', ''),
                            }
                        )
                        
                        if not profile_created:
                            profile.role = role
                            profile.department = row.get('department', '')
                            profile.alma_user_id = row.get('alma_id', '')
                            profile.phone = row.get('phone', '')
                            profile.save()

                        self.stdout.write(
                            self.style.SUCCESS(
                                f'✓ {user.username} - {role.get_name_display()}'
                            )
                        )

                    except Role.DoesNotExist:
                        self.stdout.write(
                            self.style.ERROR(
                                f'✗ Rol "{row["role"]}" no existe para usuario {row["username"]}'
                            )
                        )
                        errores += 1
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(
                                f'✗ Error con {row.get("username", "desconocido")}: {str(e)}'
                            )
                        )
                        errores += 1

        except FileNotFoundError:
            self.stdout.write(
                self.style.ERROR(f'Archivo no encontrado: {csv_file}')
            )
            return

        # Resumen
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS(f'✓ Usuarios creados: {usuarios_creados}'))
        self.stdout.write(self.style.WARNING(f'↻ Usuarios actualizados: {usuarios_actualizados}'))
        if errores > 0:
            self.stdout.write(self.style.ERROR(f'✗ Errores: {errores}'))
        self.stdout.write('='*50)