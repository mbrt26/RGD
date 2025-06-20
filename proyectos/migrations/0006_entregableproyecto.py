# Generated by Django 5.2.1 on 2025-05-23 17:52

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('proyectos', '0005_add_initial_colaboradores'),
    ]

    operations = [
        migrations.CreateModel(
            name='EntregableProyecto',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('codigo', models.CharField(max_length=20)),
                ('nombre', models.CharField(max_length=300)),
                ('fase', models.CharField(choices=[('Definición', 'Definición'), ('Planeación', 'Planeación'), ('Ejecución', 'Ejecución'), ('Entrega', 'Entrega')], max_length=50)),
                ('creador', models.CharField(max_length=200)),
                ('consolidador', models.CharField(max_length=200)),
                ('medio', models.CharField(max_length=50)),
                ('dossier_cliente', models.BooleanField(default=False)),
                ('estado', models.CharField(choices=[('pendiente', 'Pendiente'), ('en_proceso', 'En Proceso'), ('completado', 'Completado'), ('no_aplica', 'No Aplica')], default='pendiente', max_length=20)),
                ('observaciones', models.TextField(blank=True)),
                ('obligatorio', models.BooleanField(default=True)),
                ('seleccionado', models.BooleanField(default=False)),
                ('archivo', models.FileField(blank=True, null=True, upload_to='entregables/')),
                ('fecha_entrega', models.DateField(blank=True, null=True)),
                ('fecha_creacion', models.DateTimeField(auto_now_add=True)),
                ('fecha_actualizacion', models.DateTimeField(auto_now=True)),
                ('proyecto', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='entregables_proyecto', to='proyectos.proyecto')),
            ],
            options={
                'verbose_name': 'Entregable del Proyecto',
                'verbose_name_plural': 'Entregables del Proyecto',
                'ordering': ['codigo'],
                'unique_together': {('proyecto', 'codigo')},
            },
        ),
    ]
