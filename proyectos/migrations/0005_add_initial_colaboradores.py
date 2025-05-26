from django.db import migrations

def crear_colaboradores_iniciales(apps, schema_editor):
    Colaborador = apps.get_model('proyectos', 'Colaborador')
    colaboradores = [
        {
            'nombre': 'Juan Pérez',
            'cargo': 'Técnico HVAC',
            'email': 'juan.perez@rgdaire.com',
            'telefono': '300-555-0101'
        },
        {
            'nombre': 'Ana García',
            'cargo': 'Ingeniera de Proyectos',
            'email': 'ana.garcia@rgdaire.com',
            'telefono': '300-555-0102'
        },
        {
            'nombre': 'Carlos Rodríguez',
            'cargo': 'Supervisor de Instalaciones',
            'email': 'carlos.rodriguez@rgdaire.com',
            'telefono': '300-555-0103'
        },
        {
            'nombre': 'María Martínez',
            'cargo': 'Coordinadora de Mantenimiento',
            'email': 'maria.martinez@rgdaire.com',
            'telefono': '300-555-0104'
        }
    ]
    
    for colaborador_data in colaboradores:
        Colaborador.objects.create(**colaborador_data)

def eliminar_colaboradores_iniciales(apps, schema_editor):
    Colaborador = apps.get_model('proyectos', 'Colaborador')
    Colaborador.objects.all().delete()

class Migration(migrations.Migration):
    dependencies = [
        ('proyectos', '0004_colaborador_email_colaborador_telefono'),
    ]

    operations = [
        migrations.RunPython(crear_colaboradores_iniciales, eliminar_colaboradores_iniciales),
    ]