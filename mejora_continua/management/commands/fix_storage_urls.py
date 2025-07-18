"""
Management command to fix and migrate file storage URLs
"""
from django.core.management.base import BaseCommand
from django.conf import settings
from mejora_continua.models import AdjuntoSolicitud
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Fix and migrate file storage URLs for mejora_continua files'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes',
        )
        parser.add_argument(
            '--list-bucket',
            action='store_true',
            help='List all files in the bucket',
        )
        parser.add_argument(
            '--fix-missing',
            action='store_true',
            help='Attempt to fix missing file references',
        )
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== File Storage Fix Tool ===\n'))
        
        # 1. Show current configuration
        self.stdout.write('1. Current storage configuration:')
        self.stdout.write(f'   DEFAULT_FILE_STORAGE: {getattr(settings, "DEFAULT_FILE_STORAGE", "Not defined")}')
        self.stdout.write(f'   MEDIA_URL: {getattr(settings, "MEDIA_URL", "Not defined")}')
        
        if hasattr(settings, 'GS_BUCKET_NAME'):
            self.stdout.write(f'   GS_BUCKET_NAME: {settings.GS_BUCKET_NAME}')
        if hasattr(settings, 'GS_LOCATION'):
            self.stdout.write(f'   GS_LOCATION: {settings.GS_LOCATION}')
        
        # 2. List bucket contents if requested
        if options['list_bucket']:
            self.stdout.write('\n2. Listing bucket contents...')
            try:
                from google.cloud import storage
                client = storage.Client()
                bucket = client.bucket(settings.GS_BUCKET_NAME)
                
                blobs = list(bucket.list_blobs(prefix='mejora_continua'))
                if blobs:
                    self.stdout.write(f'   Found {len(blobs)} files with "mejora_continua" prefix:')
                    for blob in blobs[:10]:  # Show first 10
                        self.stdout.write(f'     - {blob.name}')
                    if len(blobs) > 10:
                        self.stdout.write(f'     ... and {len(blobs) - 10} more files')
                else:
                    self.stdout.write('   No files found with "mejora_continua" prefix')
                    
                # Also check for files without prefix
                all_blobs = list(bucket.list_blobs())
                self.stdout.write(f'   Total files in bucket: {len(all_blobs)}')
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'   Error accessing bucket: {e}'))
        
        # 3. Check database files
        self.stdout.write('\n3. Checking database file references:')
        adjuntos = AdjuntoSolicitud.objects.all()
        
        if not adjuntos.exists():
            self.stdout.write('   No files found in database')
            return
        
        broken_files = []
        working_files = []
        
        for adjunto in adjuntos:
            try:
                # Get the file path stored in database
                file_path = adjunto.archivo.name
                
                # Check if file exists using storage backend
                exists = adjunto.archivo.storage.exists(file_path)
                url = adjunto.archivo.url
                
                if exists:
                    working_files.append((adjunto, file_path, url))
                    self.stdout.write(f'   ✓ {adjunto.nombre_original} -> {file_path}')
                else:
                    broken_files.append((adjunto, file_path, url))
                    self.stdout.write(
                        self.style.WARNING(f'   ✗ {adjunto.nombre_original} -> {file_path}')
                    )
                    self.stdout.write(f'     Expected URL: {url}')
                        
            except Exception as e:
                broken_files.append((adjunto, 'ERROR', str(e)))
                self.stdout.write(
                    self.style.ERROR(f'   ERROR {adjunto.nombre_original}: {e}')
                )
        
        # 4. Summary and fix options
        self.stdout.write(f'\n4. Summary:')
        self.stdout.write(f'   Working files: {len(working_files)}')
        self.stdout.write(f'   Broken files: {len(broken_files)}')
        
        if broken_files and options['fix_missing']:
            self.stdout.write('\n5. Attempting to fix broken files...')
            
            try:
                from google.cloud import storage
                client = storage.Client()
                bucket = client.bucket(settings.GS_BUCKET_NAME)
                
                for adjunto, file_path, url in broken_files:
                    if file_path == 'ERROR':
                        continue
                        
                    self.stdout.write(f'\n   Fixing: {adjunto.nombre_original}')
                    self.stdout.write(f'   Current path: {file_path}')
                    
                    # Try different path variations
                    possible_paths = [
                        file_path,  # Original path
                        f'media/{file_path}',  # With media prefix
                        file_path.replace('media/', ''),  # Without media prefix
                    ]
                    
                    found_path = None
                    for test_path in possible_paths:
                        blob = bucket.blob(test_path)
                        if blob.exists():
                            found_path = test_path
                            break
                    
                    if found_path:
                        self.stdout.write(f'   ✓ Found file at: {found_path}')
                        
                        if not options['dry_run']:
                            # Update the database record if path is different
                            if found_path != file_path:
                                adjunto.archivo.name = found_path
                                adjunto.save()
                                self.stdout.write(f'   ✓ Updated database record')
                            else:
                                self.stdout.write(f'   ✓ File exists at correct location')
                        else:
                            self.stdout.write(f'   ✓ [DRY RUN] Would update database record')
                    else:
                        self.stdout.write(f'   ✗ File not found in any location')
                        
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'   Error during fix: {e}'))
        
        elif broken_files:
            self.stdout.write(
                '\n5. To fix broken files, run with --fix-missing flag'
            )
        
        if not broken_files:
            self.stdout.write(self.style.SUCCESS('\n✓ All files are accessible!'))
        else:
            self.stdout.write(
                self.style.WARNING(
                    f'\n⚠️  Found {len(broken_files)} broken file references'
                )
            )
            self.stdout.write(
                'Recommended next steps:\n'
                '1. Run with --list-bucket to see actual bucket contents\n'
                '2. Run with --fix-missing to attempt automatic fixes\n'
                '3. If files are missing, they may need to be re-uploaded'
            )