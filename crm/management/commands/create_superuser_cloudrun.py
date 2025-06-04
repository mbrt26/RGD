from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
import os
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Create a superuser for Cloud Run deployment'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            help='Username for the superuser',
            default=os.getenv('ADMIN_USERNAME', 'admin')
        )
        parser.add_argument(
            '--email',
            type=str,
            help='Email for the superuser',
            default=os.getenv('ADMIN_EMAIL', 'admin@rgdaire.com')
        )
        parser.add_argument(
            '--password',
            type=str,
            help='Password for the superuser',
            default=os.getenv('ADMIN_PASSWORD', 'RGDaire2024!')
        )
        parser.add_argument(
            '--update',
            action='store_true',
            help='Update existing superuser if exists',
        )

    def handle(self, *args, **options):
        User = get_user_model()
        username = options['username']
        email = options['email']
        password = options['password']
        update = options['update']
        
        self.stdout.write(f"🔑 Iniciando creación/actualización de superusuario...")
        self.stdout.write(f"   Usuario: {username}")
        self.stdout.write(f"   Email: {email}")
        
        try:
            with transaction.atomic():
                # Verificar si el usuario ya existe
                user_exists = User.objects.filter(username=username).exists()
                
                if user_exists:
                    if update:
                        user = User.objects.get(username=username)
                        user.email = email
                        user.set_password(password)
                        user.is_staff = True
                        user.is_superuser = True
                        user.is_active = True
                        user.save()
                        
                        self.stdout.write(
                            self.style.SUCCESS(f"✅ Superusuario '{username}' actualizado exitosamente")
                        )
                        logger.info(f"Superuser {username} updated successfully")
                    else:
                        self.stdout.write(
                            self.style.WARNING(f"⚠️  Usuario '{username}' ya existe. Usa --update para actualizarlo")
                        )
                        logger.warning(f"User {username} already exists")
                        return
                else:
                    # Crear nuevo superusuario
                    user = User.objects.create_user(
                        username=username,
                        email=email,
                        password=password
                    )
                    user.is_staff = True
                    user.is_superuser = True
                    user.is_active = True
                    user.save()
                    
                    self.stdout.write(
                        self.style.SUCCESS(f"✅ Superusuario '{username}' creado exitosamente")
                    )
                    logger.info(f"Superuser {username} created successfully")
                
                # Verificar la creación/actualización
                if User.objects.filter(username=username, is_superuser=True).exists():
                    self.stdout.write(
                        self.style.SUCCESS("🎉 ¡Operación completada! El superusuario está listo para usar.")
                    )
                    self.stdout.write(f"🌐 Accede en: /admin/ con las credenciales proporcionadas")
                    logger.info("Superuser operation completed successfully")
                else:
                    raise Exception("Verification failed after user creation/update")
                    
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Error al crear/actualizar superusuario: {str(e)}")
            )
            logger.error(f"Error creating/updating superuser: {str(e)}")
            raise