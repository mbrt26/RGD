"""
Middleware personalizado para desarrollo
"""
import os
import logging

logger = logging.getLogger(__name__)

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


class DebugCSRFMiddleware:
    """Middleware para depurar problemas de CSRF en producción"""
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Log información sobre CSRF antes de procesar la petición
        if request.method == 'POST':
            logger.info(f"POST request to {request.path}")
            logger.info(f"User authenticated: {request.user.is_authenticated}")
            logger.info(f"CSRF cookie present: {'csrftoken' in request.COOKIES}")
            logger.info(f"CSRF header present: {'HTTP_X_CSRFTOKEN' in request.META}")
            
            if 'HTTP_X_CSRFTOKEN' in request.META:
                logger.info(f"CSRF token from header: {request.META['HTTP_X_CSRFTOKEN'][:10]}...")
            if 'csrftoken' in request.COOKIES:
                logger.info(f"CSRF token from cookie: {request.COOKIES['csrftoken'][:10]}...")

        response = self.get_response(request)
        
        # Log información sobre la respuesta
        if request.method == 'POST' and response.status_code == 403:
            logger.error(f"403 response for POST to {request.path}")
            logger.error(f"Response headers: {dict(response.headers)}")
        
        return response