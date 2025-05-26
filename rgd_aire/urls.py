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
]

# Serve static files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
