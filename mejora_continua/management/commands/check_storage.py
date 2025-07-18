"""
Management command to check and fix file storage issues
"""
from django.core.management.base import BaseCommand
from django.conf import settings
from mejora_continua.models import AdjuntoSolicitud
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Check file storage configuration and file accessibility'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--fix-urls',
            action='store_true',
            help='Attempt to fix broken file URLs',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed information',
        )
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== Storage Configuration Check ===\n'))
        
        # 1. Show current configuration
        self.stdout.write('1. Current configuration:')
        self.stdout.write(f'   DEFAULT_FILE_STORAGE: {getattr(settings, "DEFAULT_FILE_STORAGE", "Not defined")}')
        self.stdout.write(f'   MEDIA_URL: {getattr(settings, "MEDIA_URL", "Not defined")}')
        
        if hasattr(settings, 'GS_BUCKET_NAME'):
            self.stdout.write(f'   GS_BUCKET_NAME: {settings.GS_BUCKET_NAME}')
        if hasattr(settings, 'GS_LOCATION'):
            self.stdout.write(f'   GS_LOCATION: {settings.GS_LOCATION}')
        
        # 2. Check files
        self.stdout.write('\n2. Checking uploaded files:')
        adjuntos = AdjuntoSolicitud.objects.all()
        
        if not adjuntos.exists():
            self.stdout.write('   No files found in database')
            return
        
        broken_files = []
        working_files = []
        
        for adjunto in adjuntos:
            try:
                # Check if file exists
                exists = adjunto.archivo.storage.exists(adjunto.archivo.name)
                url = adjunto.archivo.url
                
                if exists:
                    working_files.append(adjunto)
                    if options['verbose']:
                        self.stdout.write(f'   ✓ {adjunto.nombre_original} -> {url}')
                else:
                    broken_files.append(adjunto)
                    self.stdout.write(
                        self.style.WARNING(f'   ✗ {adjunto.nombre_original} -> {url}')
                    )
                    if options['verbose']:
                        self.stdout.write(f'     File path: {adjunto.archivo.name}')
                        
            except Exception as e:
                broken_files.append(adjunto)
                self.stdout.write(
                    self.style.ERROR(f'   ERROR {adjunto.nombre_original}: {e}')
                )
        
        # 3. Summary
        self.stdout.write(f'\n3. Summary:')
        self.stdout.write(f'   Working files: {len(working_files)}')
        self.stdout.write(f'   Broken files: {len(broken_files)}')
        
        if broken_files and options['fix_urls']:
            self.stdout.write('\n4. Attempting to fix broken files...')
            for adjunto in broken_files:
                # Try different path variations
                original_name = adjunto.archivo.name
                
                # Try without media/ prefix
                if original_name.startswith('media/'):
                    new_name = original_name[6:]
                    if adjunto.archivo.storage.exists(new_name):
                        self.stdout.write(f'   Found {adjunto.nombre_original} at {new_name}')
                        # Could update the database here if needed
                
                # Try with media/ prefix
                elif not original_name.startswith('media/'):
                    new_name = f'media/{original_name}'
                    if adjunto.archivo.storage.exists(new_name):
                        self.stdout.write(f'   Found {adjunto.nombre_original} at {new_name}')
        
        if broken_files:
            self.stdout.write(
                self.style.WARNING(
                    f'\nFound {len(broken_files)} broken files. '
                    'This usually indicates a configuration issue with MEDIA_URL or GS_LOCATION.'
                )
            )
            self.stdout.write(
                'Recommended actions:\n'
                '1. Check if files exist in Google Cloud Storage bucket\n'
                '2. Verify MEDIA_URL matches the actual file locations\n'
                '3. Consider running with --fix-urls to attempt automatic fixes'
            )
        else:
            self.stdout.write(self.style.SUCCESS('\nAll files are accessible! ✓'))