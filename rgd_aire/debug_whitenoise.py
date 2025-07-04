from django.http import JsonResponse
from django.conf import settings
import os

def debug_whitenoise(request):
    """Debug view to check WhiteNoise configuration"""
    
    # Check if staticfiles directory exists
    staticfiles_exists = os.path.exists(settings.STATIC_ROOT)
    staticfiles_contents = []
    if staticfiles_exists:
        try:
            for item in os.listdir(settings.STATIC_ROOT)[:10]:
                staticfiles_contents.append(item)
        except:
            pass
    
    # Check for logo file
    logo_path = os.path.join(settings.STATIC_ROOT, 'images', 'logo-rgd.png')
    logo_exists = os.path.exists(logo_path)
    
    # Check STATICFILES_DIRS
    staticfiles_dirs = getattr(settings, 'STATICFILES_DIRS', [])
    
    # Check if source static directory exists
    source_static_exists = False
    source_static_contents = []
    if staticfiles_dirs:
        source_static_dir = staticfiles_dirs[0] if staticfiles_dirs else None
        if source_static_dir and os.path.exists(source_static_dir):
            source_static_exists = True
            try:
                for item in os.listdir(source_static_dir)[:10]:
                    source_static_contents.append(item)
            except:
                pass
    
    return JsonResponse({
        'whitenoise_in_middleware': 'whitenoise.middleware.WhiteNoiseMiddleware' in settings.MIDDLEWARE,
        'middleware': settings.MIDDLEWARE,
        'static_url': settings.STATIC_URL,
        'static_root': settings.STATIC_ROOT,
        'staticfiles_dirs': staticfiles_dirs,
        'staticfiles_storage': settings.STATICFILES_STORAGE,
        'staticfiles_exists': staticfiles_exists,
        'staticfiles_contents': staticfiles_contents,
        'source_static_exists': source_static_exists,
        'source_static_contents': source_static_contents,
        'logo_exists': logo_exists,
        'logo_path': logo_path,
        'debug': settings.DEBUG,
    }, json_dumps_params={'indent': 2})