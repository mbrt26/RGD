# Generated by Django 5.2.3 on 2025-06-18 14:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('proyectos', '0009_proyecto_avance_planeado_alter_proyecto_avance'),
    ]

    operations = [
        migrations.AlterField(
            model_name='proyecto',
            name='estado',
            field=models.CharField(choices=[('pendiente', 'Pendiente'), ('en_ejecucion', 'En Ejecución'), ('atrasado', 'Atrasado'), ('finalizado', 'Finalizado')], default='pendiente', max_length=20),
        ),
    ]
