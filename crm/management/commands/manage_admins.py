"""
Comando Django para listar y gestionar administradores existentes
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db import transaction


class Command(BaseCommand):
    help = 'Lista y gestiona administradores existentes'

    def add_arguments(self, parser):
        parser.add_argument(
            '--list',
            action='store_true',
            help='Listar todos los administradores',
        )
        parser.add_argument(
            '--promote',
            type=str,
            help='Promover usuario a superadministrador',
        )
        parser.add_argument(
            '--reset-password',
            type=str,
            help='Resetear password de un usuario',
        )
        parser.add_argument(
            '--new-password',
            type=str,
            help='Nuevo password para el usuario',
        )

    def handle(self, *args, **options):
        """Gestionar administradores"""
        
        if options.get('list'):
            self.list_admins()
            return
        
        if options.get('promote'):
            self.promote_user(options['promote'])
            return
        
        if options.get('reset_password'):
            username = options['reset_password']
            new_password = options.get('new_password')
            
            if not new_password:
                self.stdout.write(
                    self.style.ERROR('❌ --new-password es requerido para resetear password')
                )
                return
            
            self.reset_user_password(username, new_password)
            return
        
        # Si no se proporciona ninguna opción, mostrar ayuda
        self.list_admins()

    def list_admins(self):
        """Listar todos los administradores"""
        self.stdout.write('\n📋 Usuarios administradores:')
        
        superusers = User.objects.filter(is_superuser=True).order_by('username')
        staff = User.objects.filter(is_staff=True, is_superuser=False).order_by('username')
        
        if not superusers.exists() and not staff.exists():
            self.stdout.write(
                self.style.WARNING('⚠️  No hay usuarios administradores configurados')
            )
            return
        
        if superusers.exists():
            self.stdout.write('\n🔴 Superusuarios (acceso completo):')
            for user in superusers:
                status = '✅ Activo' if user.is_active else '❌ Inactivo'
                last_login = user.last_login.strftime('%Y-%m-%d %H:%M') if user.last_login else 'Nunca'
                self.stdout.write(f'   • {user.username} ({user.email}) - {status} - Último login: {last_login}')
        
        if staff.exists():
            self.stdout.write('\n🟡 Staff (acceso admin limitado):')
            for user in staff:
                status = '✅ Activo' if user.is_active else '❌ Inactivo'
                last_login = user.last_login.strftime('%Y-%m-%d %H:%M') if user.last_login else 'Nunca'
                self.stdout.write(f'   • {user.username} ({user.email}) - {status} - Último login: {last_login}')
        
        # Estadísticas
        total_users = User.objects.count()
        active_users = User.objects.filter(is_active=True).count()
        
        self.stdout.write(f'\n📊 Estadísticas:')
        self.stdout.write(f'   • Total usuarios: {total_users}')
        self.stdout.write(f'   • Usuarios activos: {active_users}')
        self.stdout.write(f'   • Superusuarios: {superusers.count()}')
        self.stdout.write(f'   • Staff: {staff.count()}')

    def promote_user(self, username):
        """Promover usuario a superadministrador"""
        try:
            with transaction.atomic():
                user = User.objects.get(username=username)
                
                if user.is_superuser:
                    self.stdout.write(
                        self.style.WARNING(f'⚠️  El usuario "{username}" ya es superusuario')
                    )
                    return
                
                user.is_superuser = True
                user.is_staff = True
                user.is_active = True
                user.save()
                
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Usuario "{username}" promovido a superusuario exitosamente')
                )
                
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'❌ Usuario "{username}" no encontrado')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error al promover usuario: {str(e)}')
            )

    def reset_user_password(self, username, new_password):
        """Resetear password de un usuario"""
        try:
            with transaction.atomic():
                user = User.objects.get(username=username)
                
                if len(new_password) < 8:
                    self.stdout.write(
                        self.style.ERROR('❌ El password debe tener al menos 8 caracteres')
                    )
                    return
                
                user.set_password(new_password)
                user.save()
                
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Password del usuario "{username}" actualizado exitosamente')
                )
                
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'❌ Usuario "{username}" no encontrado')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error al resetear password: {str(e)}')
            )