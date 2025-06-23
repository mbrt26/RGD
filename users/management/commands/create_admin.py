from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction

User = get_user_model()

class Command(BaseCommand):
    help = 'Crear usuario administrador en producción'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            default='rgd_admin',
            help='Nombre de usuario (default: rgd_admin)'
        )
        parser.add_argument(
            '--email',
            type=str,
            default='admin@rgdaire.com',
            help='Email del administrador (default: admin@rgdaire.com)'
        )
        parser.add_argument(
            '--password',
            type=str,
            default='Catalina18',
            help='Contraseña del administrador (default: Catalina18)'
        )

    def handle(self, *args, **options):
        username = options['username']
        email = options['email']
        password = options['password']

        self.stdout.write(f'Creando usuario administrador: {username}')

        try:
            with transaction.atomic():
                # Verificar si el usuario ya existe
                if User.objects.filter(username=username).exists():
                    user = User.objects.get(username=username)
                    self.stdout.write(
                        self.style.WARNING(f'El usuario {username} ya existe. Actualizando...')
                    )
                    user.email = email
                    user.set_password(password)
                    user.is_staff = True
                    user.is_superuser = True
                    user.is_active = True
                    user.first_name = 'Administrador'
                    user.last_name = 'RGD AIRE'
                    user.save()
                    self.stdout.write(
                        self.style.SUCCESS(f'Usuario {username} actualizado exitosamente')
                    )
                else:
                    # Crear nuevo usuario
                    user = User.objects.create_superuser(
                        username=username,
                        email=email,
                        password=password,
                        first_name='Administrador',
                        last_name='RGD AIRE'
                    )
                    self.stdout.write(
                        self.style.SUCCESS(f'Usuario {username} creado exitosamente')
                    )

                # Verificar el usuario
                self.stdout.write(f'Usuario: {user.username}')
                self.stdout.write(f'Email: {user.email}')
                self.stdout.write(f'Es superusuario: {user.is_superuser}')
                self.stdout.write(f'Es staff: {user.is_staff}')
                self.stdout.write(f'Está activo: {user.is_active}')

                # Verificar login
                if user.check_password(password):
                    self.stdout.write(
                        self.style.SUCCESS('✅ La contraseña se configuró correctamente')
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR('❌ Error al configurar la contraseña')
                    )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error al crear/actualizar usuario: {str(e)}')
            )
            return

        self.stdout.write(
            self.style.SUCCESS(
                f'\n🎉 ¡Usuario administrador listo! Puedes hacer login con:\n'
                f'Usuario: {username}\n'
                f'Contraseña: {password}\n'
                f'URL: https://rgd-aire-dot-appsindunnova.rj.r.appspot.com/users/login/'
            )
        )