from django.apps import AppConfig


class CrmConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'crm'
    
    def ready(self):
        """
        Método que se ejecuta cuando la aplicación está lista.
        Importa los signals para registrarlos.
        """
        import crm.signals
