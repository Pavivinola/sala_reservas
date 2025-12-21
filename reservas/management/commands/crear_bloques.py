from django.core.management.base import BaseCommand
from reservas.models import TimeBlock


class Command(BaseCommand):
    help = 'Crea los bloques horarios para Lunes-Viernes y Sábados'

    def handle(self, *args, **kwargs):
        # Limpiar bloques existentes (opcional)
        if input("¿Eliminar bloques existentes? (s/n): ").lower() == 's':
            TimeBlock.objects.all().delete()
            self.stdout.write(self.style.WARNING('Bloques eliminados'))

        bloques_creados = 0

        # ========================================
        # Bloques Lunes a Viernes (9am - 8pm)
        # ========================================
        dias_semana = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday']
        
        bloques_lun_vie = [
            {'nombre': 'Bloque 1', 'inicio': '09:00', 'fin': '11:00'},
            {'nombre': 'Bloque 2', 'inicio': '11:00', 'fin': '13:00'},
            {'nombre': 'Bloque 3', 'inicio': '13:00', 'fin': '15:00'},
            {'nombre': 'Bloque 4', 'inicio': '15:00', 'fin': '17:00'},
            {'nombre': 'Bloque 5', 'inicio': '17:00', 'fin': '19:00'},
            {'nombre': 'Bloque 6', 'inicio': '19:00', 'fin': '20:00'},
        ]

        for dia in dias_semana:
            for bloque in bloques_lun_vie:
                TimeBlock.objects.create(
                    name=bloque['nombre'],
                    day_of_week=dia,
                    start_time=bloque['inicio'],
                    end_time=bloque['fin'],
                    is_active=True
                )
                bloques_creados += 1
                dia_nombre = dict(TimeBlock.DAYS_OF_WEEK).get(dia)
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✓ {dia_nombre} - {bloque["nombre"]} ({bloque["inicio"]}-{bloque["fin"]})'
                    )
                )

        # ========================================
        # Bloques Sábado (10am - 2pm)
        # ========================================
        bloques_sabado = [
            {'nombre': 'Sábado M1', 'inicio': '10:00', 'fin': '12:00'},
            {'nombre': 'Sábado M2', 'inicio': '12:00', 'fin': '14:00'},
        ]

        for bloque in bloques_sabado:
            TimeBlock.objects.create(
                name=bloque['nombre'],
                day_of_week='saturday',
                start_time=bloque['inicio'],
                end_time=bloque['fin'],
                is_active=True
            )
            bloques_creados += 1
            self.stdout.write(
                self.style.SUCCESS(
                    f'✓ Sábado - {bloque["nombre"]} ({bloque["inicio"]}-{bloque["fin"]})'
                )
            )

        # ========================================
        # Resumen
        # ========================================
        self.stdout.write(
            self.style.SUCCESS(
                f'\n🎉 Se crearon {bloques_creados} bloques horarios exitosamente'
            )
        )