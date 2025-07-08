"""
Comando para depurar por qué no se ejecutan los signals
"""
from django.core.management.base import BaseCommand
from django.db.models import signals
from crm.models import Trato
from crm.signals import trato_pre_save_handler, trato_post_save_handler
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Debug de signals de Trato'

    def handle(self, *args, **options):
        self.stdout.write("=== Debug de Signals para Trato ===\n")
        
        # 1. Verificar que los signals están conectados
        self.stdout.write("1. Verificando conexión de signals...")
        
        # Verificar pre_save
        pre_save_connected = False
        for receiver in signals.pre_save._live_receivers(sender=Trato):
            if 'trato_pre_save_handler' in str(receiver):
                pre_save_connected = True
                self.stdout.write(f"   ✅ pre_save conectado: {receiver}")
        
        if not pre_save_connected:
            self.stdout.write(self.style.ERROR("   ❌ pre_save NO está conectado"))
        
        # Verificar post_save
        post_save_connected = False
        for receiver in signals.post_save._live_receivers(sender=Trato):
            if 'trato_post_save_handler' in str(receiver):
                post_save_connected = True
                self.stdout.write(f"   ✅ post_save conectado: {receiver}")
        
        if not post_save_connected:
            self.stdout.write(self.style.ERROR("   ❌ post_save NO está conectado"))
        
        # 2. Verificar que CrmConfig está en INSTALLED_APPS
        self.stdout.write("\n2. Verificando configuración de la app...")
        from django.apps import apps
        
        crm_app = apps.get_app_config('crm')
        self.stdout.write(f"   App CRM: {crm_app}")
        self.stdout.write(f"   Clase: {crm_app.__class__.__name__}")
        
        # 3. Forzar importación de signals
        self.stdout.write("\n3. Forzando importación de signals...")
        try:
            import crm.signals
            self.stdout.write("   ✅ Signals importados correctamente")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"   ❌ Error al importar signals: {e}"))
        
        # 4. Test manual de logging
        self.stdout.write("\n4. Test de logging...")
        logger.info("[TEST] Este es un mensaje de prueba del logger")
        self.stdout.write("   Mensaje de log enviado. Verifica los logs.")
        
        # 5. Verificar nivel de logging
        self.stdout.write("\n5. Configuración de logging...")
        import logging as log_module
        root_logger = log_module.getLogger()
        self.stdout.write(f"   Nivel root logger: {log_module.getLevelName(root_logger.level)}")
        
        crm_logger = log_module.getLogger('crm.signals')
        self.stdout.write(f"   Nivel crm.signals logger: {log_module.getLevelName(crm_logger.level)}")
        
        # 6. Verificar handlers
        self.stdout.write(f"   Handlers: {[h.__class__.__name__ for h in root_logger.handlers]}")
        
        self.stdout.write("\n" + "="*50)
        self.stdout.write("Si los signals están conectados pero no ves logs [SIGNAL], verifica:")
        self.stdout.write("1. La configuración de LOGGING en settings.py")
        self.stdout.write("2. Que el nivel de log sea INFO o DEBUG")
        self.stdout.write("3. Los logs en Google Cloud Logging")