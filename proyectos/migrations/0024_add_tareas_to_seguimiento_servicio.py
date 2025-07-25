# Generated by Django 4.2.7 on 2025-07-21 21:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0003_taskimage_taskattachment_description_and_more'),
        ('proyectos', '0023_add_decision_tomada_to_servicio'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='elementoexternocomite',
            options={'ordering': ['comite', 'nombre_proyecto'], 'verbose_name': 'Elemento Externo de Comité', 'verbose_name_plural': 'Elementos Externos de Comités'},
        ),
        migrations.AddField(
            model_name='seguimientoserviciocomite',
            name='tareas',
            field=models.ManyToManyField(blank=True, help_text='Tareas creadas desde este seguimiento de servicio en comité', related_name='seguimientos_servicio_comite', to='tasks.task', verbose_name='Tareas Generadas'),
        ),
        migrations.AlterField(
            model_name='elementoexternocomite',
            name='observaciones',
            field=models.TextField(blank=True, help_text='Información adicional sobre el elemento', verbose_name='Observaciones'),
        ),
        migrations.AlterField(
            model_name='elementoexternocomite',
            name='orden_presentacion',
            field=models.PositiveIntegerField(default=999, help_text='Orden en que se presenta en el comité', verbose_name='Orden de Presentación'),
        ),
    ]
