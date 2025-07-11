# Generated by Django 5.2.3 on 2025-06-20 19:20

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Task',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200, verbose_name='título')),
                ('description', models.TextField(blank=True, verbose_name='descripción')),
                ('status', models.CharField(choices=[('pending', 'Pendiente'), ('in_progress', 'En Progreso'), ('completed', 'Completada'), ('cancelled', 'Cancelada'), ('on_hold', 'En Espera')], default='pending', max_length=20, verbose_name='estado')),
                ('priority', models.CharField(choices=[('low', 'Baja'), ('medium', 'Media'), ('high', 'Alta'), ('urgent', 'Urgente')], default='medium', max_length=10, verbose_name='prioridad')),
                ('task_type', models.CharField(choices=[('task', 'Tarea'), ('reminder', 'Recordatorio'), ('follow_up', 'Seguimiento'), ('review', 'Revisión'), ('meeting', 'Reunión'), ('call', 'Llamada'), ('email', 'Email'), ('other', 'Otro')], default='task', max_length=20, verbose_name='tipo')),
                ('due_date', models.DateTimeField(blank=True, null=True, verbose_name='fecha vencimiento')),
                ('start_date', models.DateTimeField(blank=True, null=True, verbose_name='fecha inicio')),
                ('completed_date', models.DateTimeField(blank=True, null=True, verbose_name='fecha completado')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='fecha creación')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='fecha actualización')),
                ('object_id', models.PositiveIntegerField(blank=True, null=True)),
                ('is_recurring', models.BooleanField(default=False, verbose_name='recurrente')),
                ('recurrence_pattern', models.CharField(blank=True, help_text='ej: daily, weekly, monthly', max_length=50, verbose_name='patrón recurrencia')),
                ('estimated_hours', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True, verbose_name='horas estimadas')),
                ('actual_hours', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True, verbose_name='horas reales')),
                ('reminder_sent', models.BooleanField(default=False, verbose_name='recordatorio enviado')),
                ('reminder_date', models.DateTimeField(blank=True, null=True, verbose_name='fecha recordatorio')),
                ('progress_percentage', models.PositiveIntegerField(default=0, help_text='0-100', verbose_name='porcentaje progreso')),
                ('assigned_to', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='assigned_tasks', to=settings.AUTH_USER_MODEL, verbose_name='asignado a')),
                ('content_type', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='contenttypes.contenttype', verbose_name='tipo de contenido')),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='created_tasks', to=settings.AUTH_USER_MODEL, verbose_name='creado por')),
            ],
            options={
                'verbose_name': 'Tarea',
                'verbose_name_plural': 'Tareas',
                'ordering': ['-priority', 'due_date', '-created_at'],
            },
        ),
        migrations.CreateModel(
            name='TaskAttachment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(upload_to='tasks/attachments/%Y/%m/', verbose_name='archivo')),
                ('original_name', models.CharField(max_length=255, verbose_name='nombre original')),
                ('uploaded_at', models.DateTimeField(auto_now_add=True, verbose_name='fecha subida')),
                ('file_size', models.PositiveIntegerField(blank=True, null=True, verbose_name='tamaño archivo')),
                ('task', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attachments', to='tasks.task', verbose_name='tarea')),
                ('uploaded_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='subido por')),
            ],
            options={
                'verbose_name': 'Archivo Adjunto',
                'verbose_name_plural': 'Archivos Adjuntos',
                'ordering': ['-uploaded_at'],
            },
        ),
        migrations.CreateModel(
            name='TaskCategory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='nombre')),
                ('module', models.CharField(choices=[('proyectos', 'Proyectos'), ('servicios', 'Servicios'), ('mantenimiento', 'Mantenimiento'), ('insumos', 'Insumos'), ('users', 'Usuarios'), ('general', 'General')], max_length=20, verbose_name='módulo')),
                ('description', models.TextField(blank=True, verbose_name='descripción')),
                ('color', models.CharField(default='#007bff', help_text='Color en formato hexadecimal (ej: #007bff)', max_length=7, verbose_name='color')),
                ('is_active', models.BooleanField(default=True, verbose_name='activo')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='fecha creación')),
            ],
            options={
                'verbose_name': 'Categoría de Tarea',
                'verbose_name_plural': 'Categorías de Tareas',
                'ordering': ['module', 'name'],
                'unique_together': {('name', 'module')},
            },
        ),
        migrations.AddField(
            model_name='task',
            name='category',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='tasks.taskcategory', verbose_name='categoría'),
        ),
        migrations.CreateModel(
            name='TaskComment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content', models.TextField(verbose_name='contenido')),
                ('is_internal', models.BooleanField(default=False, help_text='Solo visible para el equipo interno', verbose_name='interno')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='fecha creación')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='fecha actualización')),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='autor')),
                ('task', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='comments', to='tasks.task', verbose_name='tarea')),
            ],
            options={
                'verbose_name': 'Comentario de Tarea',
                'verbose_name_plural': 'Comentarios de Tareas',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='TaskHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action', models.CharField(choices=[('created', 'Creada'), ('updated', 'Actualizada'), ('status_changed', 'Estado Cambiado'), ('assigned', 'Asignada'), ('commented', 'Comentario Agregado'), ('completed', 'Completada'), ('cancelled', 'Cancelada')], max_length=20, verbose_name='acción')),
                ('description', models.TextField(blank=True, verbose_name='descripción')),
                ('old_value', models.TextField(blank=True, verbose_name='valor anterior')),
                ('new_value', models.TextField(blank=True, verbose_name='valor nuevo')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='fecha')),
                ('task', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='history', to='tasks.task', verbose_name='tarea')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='usuario')),
            ],
            options={
                'verbose_name': 'Historial de Tarea',
                'verbose_name_plural': 'Historiales de Tareas',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='task',
            index=models.Index(fields=['assigned_to', 'status'], name='tasks_task_assigne_b3b2bc_idx'),
        ),
        migrations.AddIndex(
            model_name='task',
            index=models.Index(fields=['due_date'], name='tasks_task_due_dat_bce847_idx'),
        ),
        migrations.AddIndex(
            model_name='task',
            index=models.Index(fields=['priority', 'status'], name='tasks_task_priorit_685c61_idx'),
        ),
        migrations.AddIndex(
            model_name='task',
            index=models.Index(fields=['category', 'status'], name='tasks_task_categor_55ce6c_idx'),
        ),
    ]
