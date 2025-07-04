"""
URL configuration for rgd_aire project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from django.contrib.auth import views as auth_views
from proyectos.api.views import actividad_detail_api
from django.http import HttpResponse
import os
from .debug_whitenoise import debug_whitenoise

# Health check endpoint para App Engine
def health_check(request):
    """Endpoint de salud para App Engine health checks"""
    try:
        # Verificación básica de la aplicación
        from django.db import connection
        from django.core.cache import cache
        
        # Test de conexión a la base de datos
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            
        # Test del cache (opcional)
        cache.set('health_check', 'ok', 10)
        cache_status = cache.get('health_check')
        
        return HttpResponse("OK", content_type="text/plain", status=200)
        
    except Exception as e:
        # En caso de error, retornar status 503
        return HttpResponse(f"UNHEALTHY: {str(e)}", content_type="text/plain", status=503)

urlpatterns = [
    # Health check para App Engine (debe estar primero)
    path('health/', health_check, name='health_check'),
    path('debug-whitenoise/', debug_whitenoise, name='debug_whitenoise'),
    
    # URLs principales de la aplicación
    path('', RedirectView.as_view(url='/crm/', permanent=True), name='home'),
    path('admin/', admin.site.urls),
    path('crm/', include('crm.urls')),
    path('proyectos/', include('proyectos.urls')),
    path('servicios/', include('servicios.urls')),
    path('mantenimiento/', include('mantenimiento.urls')),
    path('tasks/', include('tasks.urls')),
    path('mejora-continua/', include('mejora_continua.urls')),
    
    # API endpoints
    path('proyectos/api/actividades/<int:pk>/', actividad_detail_api, name='actividad_api_detail'),
    
    # Users app URLs (authentication)
    path('users/', include(('users.urls', 'users'), namespace='users')),
    
    # Redirect old auth URLs to new ones
    path('accounts/login/', RedirectView.as_view(url='/users/login/')),
    path('accounts/logout/', RedirectView.as_view(url='/users/logout/')),
    
    # Authentication URLs
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
]

# Serve static files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
