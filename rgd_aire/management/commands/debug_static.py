from django.core.management.base import BaseCommand
from django.conf import settings
from django.contrib.staticfiles import finders
import os


class Command(BaseCommand):
    help = 'Debug static files configuration and collection'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== Static Files Debug Information ==='))
        
        # Basic configuration
        self.stdout.write(f'STATIC_URL: {settings.STATIC_URL}')
        self.stdout.write(f'STATIC_ROOT: {settings.STATIC_ROOT}')
        self.stdout.write(f'STATICFILES_DIRS: {settings.STATICFILES_DIRS}')
        self.stdout.write(f'STATICFILES_STORAGE: {settings.STATICFILES_STORAGE}')
        
        # Check source directories
        self.stdout.write(self.style.SUCCESS('\n=== Source Static Directories ==='))
        for static_dir in settings.STATICFILES_DIRS:
            if os.path.exists(static_dir):
                self.stdout.write(f'✓ {static_dir} exists')
                # Count files
                file_count = sum(len(files) for _, _, files in os.walk(static_dir))
                self.stdout.write(f'  Contains {file_count} files')
                
                # Show directory structure
                for root, dirs, files in os.walk(static_dir):
                    level = root.replace(static_dir, '').count(os.sep)
                    if level < 2:  # Only show 2 levels deep
                        indent = '  ' * (level + 1)
                        self.stdout.write(f'{indent}{os.path.basename(root)}/')
                        if level < 1:  # Show files only for first level
                            for f in files[:3]:
                                self.stdout.write(f'{indent}  - {f}')
                            if len(files) > 3:
                                self.stdout.write(f'{indent}  ... and {len(files)-3} more files')
            else:
                self.stdout.write(self.style.ERROR(f'✗ {static_dir} does not exist!'))
        
        # Check collected static files
        self.stdout.write(self.style.SUCCESS('\n=== Collected Static Files (STATIC_ROOT) ==='))
        if os.path.exists(settings.STATIC_ROOT):
            self.stdout.write(f'✓ {settings.STATIC_ROOT} exists')
            
            # List top-level directories
            try:
                items = sorted(os.listdir(settings.STATIC_ROOT))
                self.stdout.write(f'Top-level directories: {items}')
                
                # Check specific directories
                for subdir in ['images', 'css', 'js', 'admin', 'proyectos']:
                    subdir_path = os.path.join(settings.STATIC_ROOT, subdir)
                    if os.path.exists(subdir_path):
                        file_count = len([f for f in os.listdir(subdir_path) if os.path.isfile(os.path.join(subdir_path, f))])
                        self.stdout.write(f'  ✓ {subdir}/: {file_count} files')
                    else:
                        self.stdout.write(self.style.WARNING(f'  ✗ {subdir}/ not found'))
                        
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error reading STATIC_ROOT: {e}'))
        else:
            self.stdout.write(self.style.ERROR(f'✗ STATIC_ROOT does not exist at {settings.STATIC_ROOT}'))
        
        # Use Django's static file finders
        self.stdout.write(self.style.SUCCESS('\n=== Django Static File Finders ==='))
        
        test_files = ['images/logo-rgd.png', 'css/style.css', 'js/script.js']
        for test_file in test_files:
            result = finders.find(test_file)
            if result:
                self.stdout.write(f'✓ {test_file} found at: {result}')
            else:
                self.stdout.write(self.style.ERROR(f'✗ {test_file} not found by finders'))
        
        # WhiteNoise configuration
        self.stdout.write(self.style.SUCCESS('\n=== WhiteNoise Configuration ==='))
        self.stdout.write(f'WHITENOISE_AUTOREFRESH: {getattr(settings, "WHITENOISE_AUTOREFRESH", "Not set")}')
        self.stdout.write(f'WHITENOISE_COMPRESS_OFFLINE: {getattr(settings, "WHITENOISE_COMPRESS_OFFLINE", "Not set")}')
        self.stdout.write(f'WHITENOISE_MAX_AGE: {getattr(settings, "WHITENOISE_MAX_AGE", "Not set")}')
        
        # Check middleware order
        self.stdout.write(self.style.SUCCESS('\n=== Middleware Order ==='))
        whitenoise_found = False
        for i, middleware in enumerate(settings.MIDDLEWARE):
            if 'whitenoise' in middleware.lower():
                self.stdout.write(self.style.SUCCESS(f'{i}: {middleware} ← WhiteNoise found!'))
                whitenoise_found = True
                if i > 1 and 'SecurityMiddleware' not in settings.MIDDLEWARE[i-1]:
                    self.stdout.write(self.style.WARNING('  Warning: WhiteNoise should be immediately after SecurityMiddleware'))
            else:
                self.stdout.write(f'{i}: {middleware}')
        
        if not whitenoise_found:
            self.stdout.write(self.style.ERROR('WhiteNoise middleware not found!'))