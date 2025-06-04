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

# Endpoint temporal para diagnóstico de DB_PASSWORD
def show_db_password(request):
    """Endpoint temporal para verificar si DB_PASSWORD se está inyectando desde Secret Manager"""
    pwd = os.environ.get('DB_PASSWORD', 'NOT_SET')
    db_user = os.environ.get('DB_USER', 'NOT_SET')
    db_name = os.environ.get('DB_NAME', 'NOT_SET')
    cloud_sql_conn = os.environ.get('CLOUD_SQL_CONNECTION_NAME', 'NOT_SET')
    
    return HttpResponse(f"""
    <h2>Diagnóstico de Variables de Entorno de Base de Datos</h2>
    <p><strong>DB_USER:</strong> {db_user}</p>
    <p><strong>DB_NAME:</strong> {db_name}</p>
    <p><strong>DB_PASSWORD:</strong> {'[CONFIGURADA]' if pwd != 'NOT_SET' else 'NOT_SET'}</p>
    <p><strong>CLOUD_SQL_CONNECTION_NAME:</strong> {cloud_sql_conn}</p>
    <p><strong>Longitud de contraseña:</strong> {len(pwd) if pwd != 'NOT_SET' else 0}</p>
    """)

urlpatterns = [
    path('', RedirectView.as_view(url='/crm/', permanent=True), name='home'),
    path('admin/', admin.site.urls),
    path('crm/', include('crm.urls')),
    path('proyectos/', include('proyectos.urls')),
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
    
    # Endpoint temporal de diagnóstico (REMOVER EN PRODUCCIÓN)
    path('debug-db-vars/', show_db_password, name='debug_db_vars'),
]

# Serve static files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
