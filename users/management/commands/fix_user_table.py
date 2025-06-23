from django.core.management.base import BaseCommand
from django.db import connection, transaction

class Command(BaseCommand):
    help = 'Agrega columnas faltantes a la tabla users_user'

    def handle(self, *args, **options):
        try:
            with connection.cursor() as cursor:
                # Verificar si las columnas existen
                cursor.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name='users_user' AND table_schema='public'
                    ORDER BY column_name;
                """)
                columns = [row[0] for row in cursor.fetchall()]
                self.stdout.write(f"Columnas existentes: {columns}")
                
                missing_columns = []
                
                # Verificar y agregar columnas faltantes
                if 'telefono' not in columns:
                    missing_columns.append('telefono')
                    cursor.execute("ALTER TABLE users_user ADD COLUMN telefono VARCHAR(20) DEFAULT '';")
                    self.stdout.write("✅ Columna 'telefono' agregada")
                    
                if 'cargo' not in columns:
                    missing_columns.append('cargo')
                    cursor.execute("ALTER TABLE users_user ADD COLUMN cargo VARCHAR(100) DEFAULT '';")
                    self.stdout.write("✅ Columna 'cargo' agregada")
                    
                if 'role_id' not in columns:
                    missing_columns.append('role_id')
                    cursor.execute("ALTER TABLE users_user ADD COLUMN role_id INTEGER REFERENCES users_role(id);")
                    self.stdout.write("✅ Columna 'role_id' agregada")
                    
                if 'created_at' not in columns:
                    missing_columns.append('created_at')
                    cursor.execute("ALTER TABLE users_user ADD COLUMN created_at TIMESTAMP WITH TIME ZONE;")
                    self.stdout.write("✅ Columna 'created_at' agregada")
                    
                if 'updated_at' not in columns:
                    missing_columns.append('updated_at')
                    cursor.execute("ALTER TABLE users_user ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE;")
                    self.stdout.write("✅ Columna 'updated_at' agregada")
                
                if missing_columns:
                    self.stdout.write(self.style.SUCCESS(f'Se agregaron las columnas: {missing_columns}'))
                else:
                    self.stdout.write(self.style.SUCCESS('Todas las columnas ya existen'))
                    
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {str(e)}'))