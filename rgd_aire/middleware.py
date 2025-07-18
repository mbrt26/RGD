"""
Middleware personalizado para desarrollo
"""
import os

class ForceHTTPMiddleware:
    """Middleware para forzar HTTP en desarrollo local"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        # Si estamos en modo de desarrollo forzado, no redirigir a HTTPS
        if os.environ.get('FORCE_HTTP') == 'true':
            # Forzar el esquema a HTTP
            request.META['wsgi.url_scheme'] = 'http'
            if 'HTTP_X_FORWARDED_PROTO' in request.META:
                del request.META['HTTP_X_FORWARDED_PROTO']
                
        response = self.get_response(request)
        return response