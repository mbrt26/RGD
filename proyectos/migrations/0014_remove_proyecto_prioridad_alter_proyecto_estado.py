# Generated by Django 5.2.3 on 2025-06-19 18:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('proyectos', '0013_add_responsable_fields_to_actividad'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='proyecto',
            name='prioridad',
        ),
        migrations.AlterField(
            model_name='proyecto',
            name='estado',
            field=models.CharField(choices=[('pendiente', 'Pendiente'), ('en_ejecucion', 'En Ejecución'), ('finalizado', 'Finalizado')], default='pendiente', max_length=20),
        ),
    ]
