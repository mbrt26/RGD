# Generated manually to fix missing columns in production database

from django.db import migrations, models, connection


def add_missing_fields(apps, schema_editor):
    """Add missing fields to users_user table if they don't exist."""
    with connection.cursor() as cursor:
        # Get table info to check existing columns
        if connection.vendor == 'postgresql':
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'users_user' AND table_schema = 'public'
            """)
        else:  # SQLite
            cursor.execute("PRAGMA table_info(users_user)")
        
        existing_columns = [row[0] if connection.vendor == 'postgresql' else row[1] for row in cursor.fetchall()]
        
        # Add telefono field if it doesn't exist
        if 'telefono' not in existing_columns:
            if connection.vendor == 'postgresql':
                cursor.execute("ALTER TABLE users_user ADD COLUMN telefono VARCHAR(20) DEFAULT '';")
            else:
                cursor.execute("ALTER TABLE users_user ADD COLUMN telefono VARCHAR(20) DEFAULT '';")
        
        # Add cargo field if it doesn't exist
        if 'cargo' not in existing_columns:
            if connection.vendor == 'postgresql':
                cursor.execute("ALTER TABLE users_user ADD COLUMN cargo VARCHAR(100) DEFAULT '';")
            else:
                cursor.execute("ALTER TABLE users_user ADD COLUMN cargo VARCHAR(100) DEFAULT '';")
        
        # Add role_id field if it doesn't exist
        if 'role_id' not in existing_columns:
            if connection.vendor == 'postgresql':
                cursor.execute("ALTER TABLE users_user ADD COLUMN role_id INTEGER REFERENCES users_role(id);")
            else:
                cursor.execute("ALTER TABLE users_user ADD COLUMN role_id INTEGER REFERENCES users_role(id);")
        
        # Add created_at field if it doesn't exist
        if 'created_at' not in existing_columns:
            if connection.vendor == 'postgresql':
                cursor.execute("ALTER TABLE users_user ADD COLUMN created_at TIMESTAMP WITH TIME ZONE;")
            else:
                cursor.execute("ALTER TABLE users_user ADD COLUMN created_at DATETIME;")
        
        # Add updated_at field if it doesn't exist
        if 'updated_at' not in existing_columns:
            if connection.vendor == 'postgresql':
                cursor.execute("ALTER TABLE users_user ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE;")
            else:
                cursor.execute("ALTER TABLE users_user ADD COLUMN updated_at DATETIME;")


def reverse_add_missing_fields(apps, schema_editor):
    """Remove the added fields."""
    with connection.cursor() as cursor:
        # Note: This is a simple reverse - in production you might want to be more careful
        fields_to_remove = ['telefono', 'cargo', 'role_id', 'created_at', 'updated_at']
        for field in fields_to_remove:
            try:
                cursor.execute(f"ALTER TABLE users_user DROP COLUMN {field};")
            except:
                pass  # Field might not exist


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0003_alter_permission_module'),
    ]

    operations = [
        migrations.RunPython(add_missing_fields, reverse_add_missing_fields),
    ]