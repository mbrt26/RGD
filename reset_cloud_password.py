#!/usr/bin/env python3
"""
Script para resetear la contraseña del usuario administrador en Cloud SQL
"""
import os
import sys
import django

# Configurar todas las variables de entorno necesarias
os.environ['DJANGO_SETTINGS_MODULE'] = 'rgd_aire.settings_appengine'
os.environ['GOOGLE_CLOUD_PROJECT'] = 'appsindunnova'
os.environ['USE_CLOUD_SQL'] = 'true'
os.environ['DJANGO_SECRET_KEY'] = 'RGD-Aire-2024-SuperSecure-Key-For-Production-9j8h7g6f5d4s3a2'
os.environ['DB_NAME'] = 'rgd_aire_db'
os.environ['DB_USER'] = 'postgres'
os.environ['DB_PASSWORD'] = 'RGD2024SecureDB!'
os.environ['CLOUD_SQL_CONNECTION_NAME'] = 'appsindunnova:us-central1:rgd-aire-db'
os.environ['GS_BUCKET_NAME'] = 'appsindunnova-rgd-aire-storage'
os.environ['DEFAULT_FROM_EMAIL'] = 'noreply@rgdaire.com'

django.setup()

from users.models import User

def reset_admin_password_cloud():
    """Resetear la contraseña del usuario administrador en Cloud SQL"""
    try:
        print("🔍 Conectando a Cloud SQL...")
        
        # Buscar o crear el usuario administrador
        admin_user, created = User.objects.get_or_create(
            username='rgd_admin',
            defaults={
                'email': 'admin@rgdaire.com',
                'is_staff': True,
                'is_superuser': True,
                'is_active': True,
            }
        )
        
        if created:
            print("✅ Usuario 'rgd_admin' creado en Cloud SQL")
        else:
            print("✅ Usuario 'rgd_admin' encontrado en Cloud SQL")
        
        # Nueva contraseña
        new_password = 'Catalina18'
        
        # Establecer la nueva contraseña
        admin_user.set_password(new_password)
        admin_user.email = 'admin@rgdaire.com'
        admin_user.is_staff = True
        admin_user.is_superuser = True
        admin_user.is_active = True
        admin_user.save()
        
        print("✅ Contraseña actualizada exitosamente en Cloud SQL")
        print(f"Usuario: {admin_user.username}")
        print(f"Email: {admin_user.email}")
        print(f"Nueva contraseña: {new_password}")
        print(f"Is Staff: {admin_user.is_staff}")
        print(f"Is Superuser: {admin_user.is_superuser}")
        print(f"Is Active: {admin_user.is_active}")
        
    except Exception as e:
        print(f"❌ Error al actualizar la contraseña en Cloud SQL: {e}")
        print(f"Tipo de error: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == '__main__':
    print("=== RESETEANDO CONTRASEÑA EN CLOUD SQL ===")
    success = reset_admin_password_cloud()
    if success:
        print("\n🎯 Credenciales actualizadas para Google Cloud:")
        print("   Usuario: rgd_admin")
        print("   Contraseña: Catalina18")
        print("   URL: https://rgd-aire-dot-appsindunnova.rj.r.appspot.com")
    else:
        print("\n❌ No se pudo resetear la contraseña en Cloud SQL")