# Generated by Django 5.2.3 on 2025-06-20 20:11

import mejora_continua.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mejora_continua', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='adjuntosolicitud',
            name='nombre_original',
            field=models.CharField(blank=True, max_length=255, verbose_name='nombre original'),
        ),
        migrations.AddField(
            model_name='adjuntosolicitud',
            name='tamaño_archivo',
            field=models.BigIntegerField(blank=True, null=True, verbose_name='tamaño del archivo'),
        ),
        migrations.AddField(
            model_name='adjuntosolicitud',
            name='tipo_archivo',
            field=models.CharField(choices=[('imagen', 'Imagen'), ('documento', 'Documento'), ('video', 'Video'), ('audio', 'Audio'), ('otro', 'Otro')], default='documento', max_length=20, verbose_name='tipo de archivo'),
        ),
        migrations.AlterField(
            model_name='adjuntosolicitud',
            name='archivo',
            field=models.FileField(upload_to=mejora_continua.models.upload_to_solicitud, verbose_name='archivo'),
        ),
    ]
