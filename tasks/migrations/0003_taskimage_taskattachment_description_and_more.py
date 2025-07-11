# Generated by Django 5.2.3 on 2025-06-20 20:13

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0002_task_centro_costos_task_contrato_mantenimiento_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='TaskImage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(help_text='Formatos soportados: JPG, PNG, GIF, WebP', upload_to='tasks/images/%Y/%m/', verbose_name='imagen')),
                ('title', models.CharField(blank=True, help_text='Título descriptivo de la imagen', max_length=200, verbose_name='título')),
                ('description', models.TextField(blank=True, help_text='Descripción detallada de la imagen', verbose_name='descripción')),
                ('taken_at', models.DateTimeField(blank=True, help_text='Fecha en que se tomó la imagen', null=True, verbose_name='fecha de captura')),
                ('location', models.CharField(blank=True, help_text='Ubicación donde se tomó la imagen', max_length=500, verbose_name='ubicación')),
                ('uploaded_at', models.DateTimeField(auto_now_add=True, verbose_name='fecha subida')),
                ('width', models.PositiveIntegerField(blank=True, null=True, verbose_name='ancho')),
                ('height', models.PositiveIntegerField(blank=True, null=True, verbose_name='alto')),
                ('file_size', models.PositiveIntegerField(blank=True, null=True, verbose_name='tamaño archivo')),
                ('is_primary', models.BooleanField(default=False, help_text='Marcar como imagen principal de la tarea', verbose_name='imagen principal')),
                ('is_public', models.BooleanField(default=False, help_text='Si está marcada, la imagen es visible para todos', verbose_name='pública')),
            ],
            options={
                'verbose_name': 'Imagen de Tarea',
                'verbose_name_plural': 'Imágenes de Tareas',
                'ordering': ['-is_primary', '-uploaded_at'],
            },
        ),
        migrations.AddField(
            model_name='taskattachment',
            name='description',
            field=models.CharField(blank=True, help_text='Descripción opcional del archivo', max_length=500, verbose_name='descripción'),
        ),
        migrations.AddField(
            model_name='taskattachment',
            name='file_type',
            field=models.CharField(choices=[('document', 'Documento'), ('image', 'Imagen'), ('video', 'Video'), ('audio', 'Audio'), ('archive', 'Archivo comprimido'), ('other', 'Otro')], default='other', max_length=20, verbose_name='tipo de archivo'),
        ),
        migrations.AddField(
            model_name='taskattachment',
            name='is_public',
            field=models.BooleanField(default=False, help_text='Si está marcado, el archivo es visible para todos', verbose_name='público'),
        ),
        migrations.AddField(
            model_name='taskattachment',
            name='mime_type',
            field=models.CharField(blank=True, max_length=100, verbose_name='tipo MIME'),
        ),
        migrations.CreateModel(
            name='TaskAttachmentGroup',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, verbose_name='nombre')),
                ('description', models.TextField(blank=True, verbose_name='descripción')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='fecha creación')),
                ('order', models.PositiveIntegerField(default=0, verbose_name='orden')),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='creado por')),
                ('task', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attachment_groups', to='tasks.task', verbose_name='tarea')),
            ],
            options={
                'verbose_name': 'Grupo de Archivos',
                'verbose_name_plural': 'Grupos de Archivos',
                'ordering': ['order', 'name'],
            },
        ),
        migrations.AddField(
            model_name='taskattachment',
            name='group',
            field=models.ForeignKey(blank=True, help_text='Grupo al que pertenece este archivo', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='grouped_attachments', to='tasks.taskattachmentgroup', verbose_name='grupo'),
        ),
        migrations.AddIndex(
            model_name='taskattachment',
            index=models.Index(fields=['task', 'file_type'], name='tasks_taska_task_id_3237bb_idx'),
        ),
        migrations.AddIndex(
            model_name='taskattachment',
            index=models.Index(fields=['uploaded_at'], name='tasks_taska_uploade_346247_idx'),
        ),
        migrations.AddField(
            model_name='taskimage',
            name='task',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='images', to='tasks.task', verbose_name='tarea'),
        ),
        migrations.AddField(
            model_name='taskimage',
            name='uploaded_by',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='subido por'),
        ),
        migrations.AlterUniqueTogether(
            name='taskattachmentgroup',
            unique_together={('task', 'name')},
        ),
        migrations.AddIndex(
            model_name='taskimage',
            index=models.Index(fields=['task', 'is_primary'], name='tasks_taski_task_id_a92240_idx'),
        ),
        migrations.AddIndex(
            model_name='taskimage',
            index=models.Index(fields=['uploaded_at'], name='tasks_taski_uploade_cb34f7_idx'),
        ),
    ]
