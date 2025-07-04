import os
import sys

# Check if static directory exists
static_dir = os.path.join(os.path.dirname(__file__), 'static')
print(f"Static directory exists: {os.path.exists(static_dir)}")

if os.path.exists(static_dir):
    print(f"Contents of static/:")
    for item in os.listdir(static_dir):
        print(f"  - {item}")
        subdir = os.path.join(static_dir, item)
        if os.path.isdir(subdir):
            print(f"    Contents of {item}/:")
            for subitem in os.listdir(subdir)[:5]:
                print(f"      - {subitem}")
else:
    print("ERROR: static/ directory not found!")

# Check Django settings
os.environ['DJANGO_SETTINGS_MODULE'] = 'rgd_aire.settings'
os.environ['GOOGLE_CLOUD_PROJECT'] = 'test'
os.environ['DJANGO_SECRET_KEY'] = 'test'
os.environ['GS_BUCKET_NAME'] = 'test'

try:
    import django
    django.setup()
    from django.conf import settings
    print(f"\nDjango STATICFILES_DIRS: {getattr(settings, 'STATICFILES_DIRS', 'NOT SET')}")
    print(f"Django STATIC_ROOT: {settings.STATIC_ROOT}")
except Exception as e:
    print(f"\nError loading Django settings: {e}")