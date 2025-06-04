#!/usr/bin/env python
"""
Management command para crear superusuario en producción
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rgd_aire.settings_production')

try:
    from django.core.management.base import BaseCommand
    from django.contrib.auth import get_user_model
except ImportError:
    # Si no podemos importar Django, configurarlo primero
    django.setup()
    from django.core.management.base import BaseCommand
    from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = 'Crear superusuario para producción'

    def add_arguments(self, parser):
        parser.add_argument('--username', default='admin', help='Username del superusuario')
        parser.add_argument('--email', default='admin@rgdaire.com', help='Email del superusuario')
        parser.add_argument('--password', default='RGDaire2024!', help='Password del superusuario')

    def handle(self, *args, **options):
        User = get_user_model()
        
        username = options['username']
        email = options['email']
        password = options['password']
        
        try:
            if User.objects.filter(username=username).exists():
                self.stdout.write(
                    self.style.WARNING(f'⚠️  El superusuario "{username}" ya existe.')
                )
                # Actualizar contraseña
                user = User.objects.get(username=username)
                user.set_password(password)
                user.save()
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Contraseña actualizada para "{username}"')
                )
            else:
                User.objects.create_superuser(
                    username=username,
                    email=email,
                    password=password
                )
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Superusuario "{username}" creado exitosamente.')
                )
            
            self.stdout.write('🔑 Credenciales de acceso:')
            self.stdout.write(f'   Usuario: {username}')
            self.stdout.write(f'   Email: {email}')
            self.stdout.write(f'   Contraseña: {password}')
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error al crear superusuario: {str(e)}')
            )
            sys.exit(1)