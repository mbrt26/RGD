"""
Comando Django para crear un superusuario de forma segura en App Engine
"""
import os
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db import transaction


class Command(BaseCommand):
    help = 'Crea un superusuario de forma segura para App Engine'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            help='Nombre de usuario del administrador',
        )
        parser.add_argument(
            '--email',
            type=str,
            help='Email del administrador',
        )
        parser.add_argument(
            '--password',
            type=str,
            help='Contraseña del administrador',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Forzar la creación incluso si el usuario ya existe',
        )

    def handle(self, *args, **options):
        """Crear superusuario de forma segura"""
        
        # Obtener credenciales desde argumentos o variables de entorno
        username = options.get('username') or os.environ.get('ADMIN_USERNAME', 'admin')
        email = options.get('email') or os.environ.get('ADMIN_EMAIL', 'admin@rgdaire.com')
        password = options.get('password') or os.environ.get('ADMIN_PASSWORD')
        
        if not password:
            self.stdout.write(
                self.style.ERROR('❌ Password es requerido. Proporciona --password o configura ADMIN_PASSWORD')
            )
            return
        
        # Validar que el password sea seguro
        if len(password) < 8:
            self.stdout.write(
                self.style.ERROR('❌ El password debe tener al menos 8 caracteres')
            )
            return
        
        try:
            with transaction.atomic():
                # Verificar si el usuario ya existe
                if User.objects.filter(username=username).exists():
                    if not options.get('force'):
                        self.stdout.write(
                            self.style.WARNING(f'⚠️  El usuario "{username}" ya existe. Usa --force para actualizarlo.')
                        )
                        # Verificar si es superusuario
                        user = User.objects.get(username=username)
                        if user.is_superuser:
                            self.stdout.write(
                                self.style.SUCCESS(f'✅ El usuario "{username}" ya es superusuario')
                            )
                        else:
                            # Convertir en superusuario
                            user.is_superuser = True
                            user.is_staff = True
                            user.save()
                            self.stdout.write(
                                self.style.SUCCESS(f'✅ Usuario "{username}" convertido a superusuario')
                            )
                        return
                    else:
                        # Actualizar usuario existente
                        user = User.objects.get(username=username)
                        user.set_password(password)
                        user.email = email
                        user.is_superuser = True
                        user.is_staff = True
                        user.is_active = True
                        user.save()
                        self.stdout.write(
                            self.style.SUCCESS(f'✅ Superusuario "{username}" actualizado exitosamente')
                        )
                        return
                
                # Crear nuevo superusuario
                user = User.objects.create_superuser(
                    username=username,
                    email=email,
                    password=password
                )
                
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Superusuario "{username}" creado exitosamente')
                )
                self.stdout.write(f'   Username: {username}')
                self.stdout.write(f'   Email: {email}')
                self.stdout.write(f'   Superusuario: ✅')
                self.stdout.write(f'   Staff: ✅')
                self.stdout.write(f'   Activo: ✅')
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error al crear superusuario: {str(e)}')
            )
            raise e

    def show_admin_info(self):
        """Mostrar información de todos los administradores"""
        admins = User.objects.filter(is_superuser=True)
        
        if not admins.exists():
            self.stdout.write(
                self.style.WARNING('⚠️  No hay superusuarios configurados')
            )
            return
        
        self.stdout.write('\n📋 Superusuarios configurados:')
        for admin in admins:
            status = '✅ Activo' if admin.is_active else '❌ Inactivo'
            self.stdout.write(f'   • {admin.username} ({admin.email}) - {status}')