# Generated by Django 5.2.3

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('proyectos', '0020_add_task_relation_to_seguimiento'),
    ]

    operations = [
        migrations.AddField(
            model_name='elementoexternocomite',
            name='cliente',
            field=models.CharField(
                verbose_name='Cliente',
                max_length=200,
                default='',
                help_text='Nombre del cliente'
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='elementoexternocomite',
            name='logros_periodo',
            field=models.TextField(
                verbose_name='Logros del Período',
                blank=True,
                help_text='Principales logros y avances desde el último comité'
            ),
        ),
        migrations.AddField(
            model_name='elementoexternocomite',
            name='dificultades',
            field=models.TextField(
                verbose_name='Dificultades',
                blank=True,
                help_text='Problemas, obstáculos o riesgos identificados'
            ),
        ),
        migrations.AddField(
            model_name='elementoexternocomite',
            name='acciones_requeridas',
            field=models.TextField(
                verbose_name='Acciones Requeridas',
                blank=True,
                help_text='Acciones específicas a tomar para resolver dificultades'
            ),
        ),
        migrations.AddField(
            model_name='elementoexternocomite',
            name='decision_tomada',
            field=models.TextField(
                verbose_name='Decisión Tomada',
                blank=True,
                help_text='Decisiones tomadas o pendientes de tomar'
            ),
        ),
        migrations.RemoveField(
            model_name='elementoexternocomite',
            name='fecha_proximo_hito',
        ),
        migrations.RemoveField(
            model_name='elementoexternocomite',
            name='requiere_decision',
        ),
    ]