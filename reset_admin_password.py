#!/usr/bin/env python3
"""
Script para resetear la contraseña del usuario administrador
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rgd_aire.settings')
django.setup()

from users.models import User

def reset_admin_password():
    """Resetear la contraseña del usuario administrador"""
    try:
        # Buscar el usuario administrador
        admin_user = User.objects.get(username='rgd_admin')
        
        # Nueva contraseña
        new_password = 'Catalina18'
        
        # Establecer la nueva contraseña
        admin_user.set_password(new_password)
        admin_user.save()
        
        print("✅ Contraseña actualizada exitosamente")
        print(f"Usuario: {admin_user.username}")
        print(f"Email: {admin_user.email}")
        print(f"Nueva contraseña: {new_password}")
        print(f"Is Staff: {admin_user.is_staff}")
        print(f"Is Superuser: {admin_user.is_superuser}")
        print(f"Is Active: {admin_user.is_active}")
        
    except User.DoesNotExist:
        print("❌ Usuario 'rgd_admin' no encontrado")
        return False
    except Exception as e:
        print(f"❌ Error al actualizar la contraseña: {e}")
        return False
    
    return True

if __name__ == '__main__':
    print("=== RESETEANDO CONTRASEÑA DEL ADMINISTRADOR ===")
    success = reset_admin_password()
    if success:
        print("\n🎯 Ahora puedes iniciar sesión con:")
        print("   Usuario: rgd_admin")
        print("   Contraseña: Catalina18")
    else:
        print("\n❌ No se pudo resetear la contraseña")