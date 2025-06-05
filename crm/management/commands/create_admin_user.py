#!/usr/bin/env python
"""
Management command para crear superusuario en App Engine
Optimizado para usar variables de entorno y ser más seguro
Uso: python manage.py create_admin_user
"""
import os
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError


class Command(BaseCommand):
    help = 'Crear superusuario para App Engine usando variables de entorno'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username', 
            default=os.environ.get('ADMIN_USERNAME', 'admin'),
            help='Username del superusuario (default: admin o ADMIN_USERNAME env var)'
        )
        parser.add_argument(
            '--email', 
            default=os.environ.get('ADMIN_EMAIL', 'admin@rgdaire.com'),
            help='Email del superusuario (default: admin@rgdaire.com o ADMIN_EMAIL env var)'
        )
        parser.add_argument(
            '--password', 
            default=os.environ.get('ADMIN_PASSWORD', 'RGDaire2024!'),
            help='Password del superusuario (default: RGDaire2024! o ADMIN_PASSWORD env var)'
        )
        parser.add_argument(
            '--force-update',
            action='store_true',
            help='Forzar actualización si el usuario ya existe'
        )

    def handle(self, *args, **options):
        User = get_user_model()
        
        username = options['username']
        email = options['email']
        password = options['password']
        force_update = options['force_update']
        
        # Validaciones básicas
        if not username or len(username) < 3:
            self.stdout.write(
                self.style.ERROR('❌ Username debe tener al menos 3 caracteres')
            )
            return
        
        if not email or '@' not in email:
            self.stdout.write(
                self.style.ERROR('❌ Email inválido')
            )
            return
        
        if not password or len(password) < 8:
            self.stdout.write(
                self.style.ERROR('❌ Password debe tener al menos 8 caracteres')
            )
            return
        
        try:
            # Verificar si el usuario ya existe
            user_exists = User.objects.filter(username=username).exists()
            
            if user_exists and not force_update:
                user = User.objects.get(username=username)
                self.stdout.write(
                    self.style.WARNING(f'⚠️  El superusuario "{username}" ya existe.')
                )
                self.stdout.write(f'   Email actual: {user.email}')
                self.stdout.write(f'   Es superusuario: {user.is_superuser}')
                self.stdout.write(f'   Está activo: {user.is_active}')
                self.stdout.write('   Usa --force-update para actualizar')
                return
            
            if user_exists and force_update:
                # Actualizar usuario existente
                user = User.objects.get(username=username)
                user.email = email
                user.set_password(password)
                user.is_superuser = True
                user.is_staff = True
                user.is_active = True
                user.save()
                
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Superusuario "{username}" actualizado exitosamente')
                )
            else:
                # Crear nuevo usuario
                user = User.objects.create_superuser(
                    username=username,
                    email=email,
                    password=password
                )
                
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Superusuario "{username}" creado exitosamente')
                )
            
            # Mostrar información de acceso
            self.stdout.write('')
            self.stdout.write('🔑 Credenciales de acceso al panel administrativo:')
            self.stdout.write(f'   🌐 URL: https://your-app.appspot.com/admin/')
            self.stdout.write(f'   👤 Usuario: {username}')
            self.stdout.write(f'   📧 Email: {email}')
            self.stdout.write(f'   🔐 Contraseña: {password}')
            self.stdout.write('')
            self.stdout.write('💡 Tip: Cambia la contraseña después del primer login')
            
            # Información adicional en App Engine
            if os.environ.get('GAE_ENV'):
                self.stdout.write('')
                self.stdout.write('🌟 Ejecutándose en Google App Engine')
                project_id = os.environ.get('GOOGLE_CLOUD_PROJECT', 'unknown')
                self.stdout.write(f'   📋 Proyecto: {project_id}')
            
        except ValidationError as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error de validación: {str(e)}')
            )
            return
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error inesperado al crear superusuario: {str(e)}')
            )
            # En producción, no mostrar el stack trace completo
            if os.environ.get('DEBUG', 'False').lower() == 'true':
                raise e
            return