# Generated by Django 5.2.3 on 2025-07-23 16:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('proyectos', '0024_add_tareas_to_seguimiento_servicio'),
    ]

    operations = [
        migrations.AddField(
            model_name='seguimientoserviciocomite',
            name='observaciones',
            field=models.TextField(blank=True, help_text='Observaciones consolidadas del seguimiento', verbose_name='Observaciones'),
        ),
    ]
