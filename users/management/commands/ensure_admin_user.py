from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
import os

User = get_user_model()

class Command(BaseCommand):
    help = 'Asegura que el usuario administrador existe con la contraseña correcta'

    def handle(self, *args, **options):
        username = os.environ.get('ADMIN_USERNAME', 'rgd_admin')
        email = os.environ.get('ADMIN_EMAIL', 'admin@rgdaire.com')
        password = os.environ.get('ADMIN_PASSWORD', 'Catalina18')

        try:
            # Buscar o crear el usuario administrador
            admin_user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': email,
                    'is_staff': True,
                    'is_superuser': True,
                    'is_active': True,
                }
            )
            
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Usuario administrador "{username}" creado exitosamente')
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Usuario administrador "{username}" ya existe')
                )
            
            # Actualizar la contraseña y otros campos
            admin_user.set_password(password)
            admin_user.email = email
            admin_user.is_staff = True
            admin_user.is_superuser = True
            admin_user.is_active = True
            admin_user.save()
            
            self.stdout.write(
                self.style.SUCCESS(f'✅ Contraseña actualizada para "{username}"')
            )
            self.stdout.write(
                self.style.SUCCESS(f'📧 Email: {email}')
            )
            self.stdout.write(
                self.style.SUCCESS(f'🔐 Contraseña: {password}')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error al crear/actualizar usuario administrador: {e}')
            )
            raise e