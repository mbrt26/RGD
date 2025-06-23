from django.core.management.base import BaseCommand
from django.db import transaction
from crm.models import ConfiguracionOferta, Trato


class Command(BaseCommand):
    help = 'Inicializa la configuración de numeración de ofertas con el siguiente número basado en las ofertas existentes'

    def add_arguments(self, parser):
        parser.add_argument(
            '--siguiente-numero',
            type=int,
            help='Especifica manualmente el siguiente número de oferta a usar',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Fuerza la actualización incluso si ya existe una configuración',
        )

    def handle(self, *args, **options):
        siguiente_numero = options.get('siguiente_numero')
        force = options.get('force', False)
        
        # Verificar si ya existe configuración
        config_exists = ConfiguracionOferta.objects.exists()
        if config_exists and not force:
            self.stdout.write(
                self.style.WARNING(
                    'Ya existe una configuración de numeración de ofertas. '
                    'Use --force para sobrescribir.'
                )
            )
            return

        with transaction.atomic():
            if siguiente_numero is not None:
                # Usar el número especificado manualmente
                if siguiente_numero < 1:
                    self.stdout.write(
                        self.style.ERROR('El siguiente número debe ser mayor a 0')
                    )
                    return
                numero_a_usar = siguiente_numero
                self.stdout.write(
                    f'Usando el número especificado manualmente: {numero_a_usar}'
                )
            else:
                # Calcular automáticamente basado en ofertas existentes
                ultimo_trato = Trato.objects.exclude(numero_oferta='').order_by('-numero_oferta').first()
                
                if ultimo_trato and ultimo_trato.numero_oferta:
                    try:
                        ultimo_numero = int(ultimo_trato.numero_oferta)
                        numero_a_usar = ultimo_numero + 1
                        self.stdout.write(
                            f'Última oferta encontrada: #{ultimo_trato.numero_oferta}'
                        )
                        self.stdout.write(
                            f'Siguiente número calculado: {numero_a_usar}'
                        )
                    except ValueError:
                        numero_a_usar = 1
                        self.stdout.write(
                            self.style.WARNING(
                                f'No se pudo convertir el número de oferta "{ultimo_trato.numero_oferta}" a entero. '
                                f'Usando valor por defecto: {numero_a_usar}'
                            )
                        )
                else:
                    numero_a_usar = 1
                    self.stdout.write('No se encontraron ofertas existentes. Usando valor por defecto: 1')

            # Crear o actualizar la configuración
            if config_exists:
                config = ConfiguracionOferta.objects.first()
                config.siguiente_numero = numero_a_usar
                config.save()
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Configuración actualizada. Siguiente número de oferta: {numero_a_usar:04d}'
                    )
                )
            else:
                ConfiguracionOferta.objects.create(siguiente_numero=numero_a_usar)
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Configuración creada. Siguiente número de oferta: {numero_a_usar:04d}'
                    )
                )

            # Mostrar resumen
            self.stdout.write('\n' + '='*50)
            self.stdout.write('RESUMEN DE LA INICIALIZACIÓN')
            self.stdout.write('='*50)
            self.stdout.write(f'Siguiente número de oferta configurado: {numero_a_usar:04d}')
            self.stdout.write('Las nuevas ofertas usarán esta numeración automáticamente.')
            self.stdout.write('Puede modificar este valor desde el panel de administración de Django.')
            self.stdout.write('='*50)