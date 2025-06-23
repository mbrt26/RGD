from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse, HttpResponseForbidden
from django.db.models import Q, Count, Case, When, IntegerField, F
from django.utils import timezone
from django.core.paginator import Paginator
from datetime import timedelta
from .models import Task, TaskCategory, TaskComment, TaskAttachment, TaskHistory, TaskImage, TaskAttachmentGroup
from .forms import (
    TaskForm, TaskQuickCreateForm, TaskUpdateForm, TaskCategoryForm, 
    TaskCommentForm, TaskAttachmentForm, TaskFilterForm, TaskImageForm,
    MultipleTaskAttachmentForm, MultipleTaskImageForm, TaskAttachmentGroupForm
)

def user_has_tasks_permission(user, action='view'):
    """Verifica si el usuario tiene permisos en el módulo de tareas."""
    return user.is_superuser or user.has_module_permission('tasks', action)

class TaskPermissionMixin(UserPassesTestMixin):
    """Mixin para verificar permisos de tareas."""
    permission_action = 'view'
    
    def test_func(self):
        return user_has_tasks_permission(self.request.user, self.permission_action)

@login_required
def tasks_dashboard(request):
    """Dashboard principal de tareas con estadísticas y resumen."""
    user = request.user
    
    # Estadísticas generales
    if user.is_superuser or user_has_tasks_permission(user, 'view'):
        # Superusuario ve todas las tareas
        all_tasks = Task.objects.all()
        user_tasks = user.assigned_tasks.all()
    else:
        # Usuario normal solo ve sus tareas
        all_tasks = user.assigned_tasks.all()
        user_tasks = all_tasks
    
    # Estadísticas básicas
    total_tasks = all_tasks.count()
    pending_tasks = all_tasks.filter(status='pending').count()
    in_progress_tasks = all_tasks.filter(status='in_progress').count()
    completed_tasks = all_tasks.filter(status='completed').count()
    overdue_tasks = all_tasks.filter(
        due_date__lt=timezone.now(),
        status__in=['pending', 'in_progress']
    ).count()
    
    # Tareas por prioridad
    urgent_tasks = all_tasks.filter(priority='urgent', status__in=['pending', 'in_progress']).count()
    high_tasks = all_tasks.filter(priority='high', status__in=['pending', 'in_progress']).count()
    
    # Tareas del usuario
    my_pending = user_tasks.filter(status='pending').count()
    my_in_progress = user_tasks.filter(status='in_progress').count()
    my_overdue = user_tasks.filter(
        due_date__lt=timezone.now(),
        status__in=['pending', 'in_progress']
    ).count()
    
    # Tareas próximas a vencer (próximos 7 días)
    next_week = timezone.now() + timedelta(days=7)
    upcoming_tasks = user_tasks.filter(
        due_date__lte=next_week,
        due_date__gte=timezone.now(),
        status__in=['pending', 'in_progress']
    ).order_by('due_date')[:5]
    
    # Tareas recientes
    recent_tasks = user_tasks.order_by('-created_at')[:5]
    
    # Tareas por categoría
    tasks_by_category = all_tasks.values('category__name', 'category__color').annotate(
        count=Count('id')
    ).order_by('-count')[:5]
    
    # Tareas por centro de costos
    tasks_by_centro_costos = all_tasks.exclude(
        Q(centro_costos='') & Q(proyecto_relacionado__centro_costos='')
    ).extra(
        select={
            'centro_costos_display': """
                CASE 
                    WHEN tasks_task.centro_costos != '' THEN tasks_task.centro_costos
                    ELSE proyectos_proyecto.centro_costos
                END
            """
        }
    ).values('centro_costos_display').annotate(
        count=Count('id')
    ).order_by('-count')[:5]
    
    # Tareas por módulo
    tasks_by_module = all_tasks.aggregate(
        proyectos=Count('id', filter=Q(proyecto_relacionado__isnull=False)),
        servicios=Count('id', filter=Q(solicitud_servicio__isnull=False)),
        mantenimiento=Count('id', filter=Q(contrato_mantenimiento__isnull=False)),
        general=Count('id', filter=Q(
            proyecto_relacionado__isnull=True,
            solicitud_servicio__isnull=True,
            contrato_mantenimiento__isnull=True
        ))
    )
    
    # Actividad reciente
    recent_activity = TaskHistory.objects.filter(
        task__in=all_tasks
    ).select_related('task', 'user').order_by('-created_at')[:10]
    
    context = {
        'total_tasks': total_tasks,
        'pending_tasks': pending_tasks,
        'in_progress_tasks': in_progress_tasks,
        'completed_tasks': completed_tasks,
        'overdue_tasks': overdue_tasks,
        'urgent_tasks': urgent_tasks,
        'high_tasks': high_tasks,
        'my_pending': my_pending,
        'my_in_progress': my_in_progress,
        'my_overdue': my_overdue,
        'upcoming_tasks': upcoming_tasks,
        'recent_tasks': recent_tasks,
        'tasks_by_category': tasks_by_category,
        'tasks_by_centro_costos': tasks_by_centro_costos,
        'tasks_by_module': tasks_by_module,
        'recent_activity': recent_activity,
        'can_create': user_has_tasks_permission(user, 'add'),
        'can_manage': user_has_tasks_permission(user, 'change'),
    }
    
    return render(request, 'tasks/dashboard.html', context)

class TaskListView(LoginRequiredMixin, ListView):
    """Vista para listar tareas con filtros."""
    model = Task
    template_name = 'tasks/task_list.html'
    context_object_name = 'tasks'
    paginate_by = 20
    
    def get_queryset(self):
        user = self.request.user
        
        # Base queryset según permisos
        if user.is_superuser or user_has_tasks_permission(user, 'view'):
            queryset = Task.objects.all()
        else:
            queryset = user.assigned_tasks.all()
        
        queryset = queryset.select_related('assigned_to', 'created_by', 'category').order_by('-created_at')
        
        # Aplicar filtros del formulario
        form = TaskFilterForm(self.request.GET, user=user)
        if form.is_valid():
            # Filtro de búsqueda
            search = form.cleaned_data.get('search')
            if search:
                queryset = queryset.filter(
                    Q(title__icontains=search) | Q(description__icontains=search)
                )
            
            # Filtros de campo
            if form.cleaned_data.get('status'):
                queryset = queryset.filter(status=form.cleaned_data['status'])
            
            if form.cleaned_data.get('priority'):
                queryset = queryset.filter(priority=form.cleaned_data['priority'])
            
            if form.cleaned_data.get('task_type'):
                queryset = queryset.filter(task_type=form.cleaned_data['task_type'])
            
            if form.cleaned_data.get('assigned_to'):
                queryset = queryset.filter(assigned_to=form.cleaned_data['assigned_to'])
            
            if form.cleaned_data.get('category'):
                queryset = queryset.filter(category=form.cleaned_data['category'])
            
            # Filtros de fecha
            if form.cleaned_data.get('due_date_from'):
                queryset = queryset.filter(due_date__gte=form.cleaned_data['due_date_from'])
            
            if form.cleaned_data.get('due_date_to'):
                queryset = queryset.filter(due_date__lte=form.cleaned_data['due_date_to'])
            
            # Filtro de vencidas
            if form.cleaned_data.get('overdue_only'):
                queryset = queryset.filter(
                    due_date__lt=timezone.now(),
                    status__in=['pending', 'in_progress']
                )
            
            # Filtro de mis tareas
            if form.cleaned_data.get('my_tasks_only'):
                queryset = queryset.filter(assigned_to=user)
            
            # Filtro por centro de costos
            centro_costos = form.cleaned_data.get('centro_costos')
            if centro_costos:
                queryset = queryset.filter(
                    Q(centro_costos__icontains=centro_costos) |
                    Q(proyecto_relacionado__centro_costos__icontains=centro_costos)
                )
            
            # Filtro por módulo
            modulo = form.cleaned_data.get('modulo')
            if modulo:
                if modulo == 'proyectos':
                    queryset = queryset.filter(proyecto_relacionado__isnull=False)
                elif modulo == 'servicios':
                    queryset = queryset.filter(solicitud_servicio__isnull=False)
                elif modulo == 'mantenimiento':
                    queryset = queryset.filter(contrato_mantenimiento__isnull=False)
                elif modulo == 'general':
                    queryset = queryset.filter(
                        proyecto_relacionado__isnull=True,
                        solicitud_servicio__isnull=True,
                        contrato_mantenimiento__isnull=True
                    )
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter_form'] = TaskFilterForm(self.request.GET, user=self.request.user)
        context['can_create'] = user_has_tasks_permission(self.request.user, 'add')
        context['user'] = self.request.user
        return context

class TaskDetailView(LoginRequiredMixin, DetailView):
    """Vista para ver detalles de una tarea."""
    model = Task
    template_name = 'tasks/task_detail.html'
    context_object_name = 'task'
    
    def get_object(self):
        task = get_object_or_404(Task, pk=self.kwargs['pk'])
        
        # Verificar permisos
        if not task.can_be_viewed_by(self.request.user):
            raise PermissionError(_('No tienes permisos para ver esta tarea.'))
        
        return task
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        task = self.object
        user = self.request.user
        
        # Formularios para comentarios y archivos
        context['comment_form'] = TaskCommentForm()
        context['attachment_form'] = TaskAttachmentForm(task=task)
        context['multiple_attachment_form'] = MultipleTaskAttachmentForm(task=task)
        context['image_form'] = TaskImageForm()
        context['multiple_image_form'] = MultipleTaskImageForm()
        context['group_form'] = TaskAttachmentGroupForm()
        
        # Comentarios
        context['comments'] = task.comments.select_related('author').order_by('-created_at')
        
        # Archivos adjuntos organizados por tipo
        attachments = task.attachments.select_related('uploaded_by', 'group').order_by('-uploaded_at')
        context['attachments'] = attachments
        context['attachments_by_type'] = {
            'documents': attachments.filter(file_type='document'),
            'images': attachments.filter(file_type='image'),
            'videos': attachments.filter(file_type='video'),
            'audio': attachments.filter(file_type='audio'),
            'archives': attachments.filter(file_type='archive'),
            'others': attachments.filter(file_type='other'),
        }
        
        # Imágenes específicas
        context['images'] = task.images.select_related('uploaded_by').order_by('-is_primary', '-uploaded_at')
        context['primary_image'] = task.images.filter(is_primary=True).first()
        
        # Grupos de archivos
        context['attachment_groups'] = task.attachment_groups.prefetch_related('grouped_attachments').order_by('order', 'name')
        
        # Historial
        context['history'] = task.history.select_related('user').order_by('-created_at')[:10]
        
        # Permisos
        context['can_edit'] = task.can_be_edited_by(user)
        context['can_comment'] = user == task.assigned_to or user == task.created_by or user.is_superuser
        context['can_attach'] = context['can_comment']
        
        return context

class TaskCreateView(LoginRequiredMixin, CreateView):
    """Vista para crear tareas."""
    model = Task
    form_class = TaskForm
    template_name = 'tasks/task_form.html'
    
    def dispatch(self, request, *args, **kwargs):
        if not user_has_tasks_permission(request.user, 'add'):
            return HttpResponseForbidden(_('No tienes permisos para crear tareas.'))
        return super().dispatch(request, *args, **kwargs)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        
        # Crear entrada en el historial
        TaskHistory.objects.create(
            task=self.object,
            action='created',
            user=self.request.user,
            description=f'Tarea creada y asignada a {self.object.assigned_to.get_full_name_display()}'
        )
        
        messages.success(self.request, _('Tarea creada exitosamente.'))
        return response
    
    def get_success_url(self):
        return reverse('tasks:task_detail', kwargs={'pk': self.object.pk})

class TaskUpdateView(LoginRequiredMixin, UpdateView):
    """Vista para actualizar tareas."""
    model = Task
    form_class = TaskUpdateForm
    template_name = 'tasks/task_form.html'
    
    def get_object(self):
        task = get_object_or_404(Task, pk=self.kwargs['pk'])
        
        # Verificar permisos
        if not task.can_be_edited_by(self.request.user):
            raise PermissionError(_('No tienes permisos para editar esta tarea.'))
        
        return task
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        # Detectar cambios importantes
        old_task = Task.objects.get(pk=self.object.pk)
        
        response = super().form_valid(form)
        
        # Registrar cambios en el historial
        changes = []
        if old_task.status != self.object.status:
            changes.append(f'Estado: {old_task.get_status_display()} → {self.object.get_status_display()}')
        
        if old_task.assigned_to != self.object.assigned_to:
            changes.append(f'Asignado: {old_task.assigned_to.get_full_name_display()} → {self.object.assigned_to.get_full_name_display()}')
        
        if old_task.priority != self.object.priority:
            changes.append(f'Prioridad: {old_task.get_priority_display()} → {self.object.get_priority_display()}')
        
        if changes:
            TaskHistory.objects.create(
                task=self.object,
                action='updated',
                user=self.request.user,
                description='; '.join(changes)
            )
        
        messages.success(self.request, _('Tarea actualizada exitosamente.'))
        return response
    
    def get_success_url(self):
        return reverse('tasks:task_detail', kwargs={'pk': self.object.pk})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['editing'] = True
        return context

class TaskDeleteView(LoginRequiredMixin, DeleteView):
    """Vista para eliminar tareas."""
    model = Task
    template_name = 'tasks/task_confirm_delete.html'
    success_url = reverse_lazy('tasks:task_list')
    
    def get_object(self):
        task = get_object_or_404(Task, pk=self.kwargs['pk'])
        
        # Verificar permisos
        if not (task.created_by == self.request.user or self.request.user.is_superuser or 
                user_has_tasks_permission(self.request.user, 'delete')):
            raise PermissionError(_('No tienes permisos para eliminar esta tarea.'))
        
        return task
    
    def delete(self, request, *args, **kwargs):
        task = self.get_object()
        messages.success(request, f'Tarea "{task.title}" eliminada exitosamente.')
        return super().delete(request, *args, **kwargs)

# VISTAS PARA COMENTARIOS Y ARCHIVOS

@login_required
def add_task_comment(request, task_id):
    """Agregar comentario a una tarea."""
    task = get_object_or_404(Task, pk=task_id)
    
    # Verificar permisos
    if not (request.user == task.assigned_to or request.user == task.created_by or request.user.is_superuser):
        return JsonResponse({'error': _('No tienes permisos para comentar en esta tarea.')}, status=403)
    
    if request.method == 'POST':
        form = TaskCommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.task = task
            comment.author = request.user
            comment.save()
            
            # Registrar en historial
            TaskHistory.objects.create(
                task=task,
                action='commented',
                user=request.user,
                description=f'Comentario agregado: {comment.content[:50]}...'
            )
            
            messages.success(request, _('Comentario agregado exitosamente.'))
            return redirect('tasks:task_detail', pk=task_id)
    
    return redirect('tasks:task_detail', pk=task_id)

@login_required
def add_task_attachment(request, task_id):
    """Agregar archivo adjunto a una tarea."""
    task = get_object_or_404(Task, pk=task_id)
    
    # Verificar permisos
    if not (request.user == task.assigned_to or request.user == task.created_by or request.user.is_superuser):
        return JsonResponse({'error': _('No tienes permisos para agregar archivos a esta tarea.')}, status=403)
    
    if request.method == 'POST':
        form = TaskAttachmentForm(request.POST, request.FILES, task=task)
        if form.is_valid():
            attachment = form.save(commit=False)
            attachment.task = task
            attachment.uploaded_by = request.user
            attachment.save()
            
            # Registrar en historial
            TaskHistory.objects.create(
                task=task,
                action='updated',
                user=request.user,
                description=f'Archivo agregado: {attachment.original_name}'
            )
            
            messages.success(request, _('Archivo adjunto agregado exitosamente.'))
            return redirect('tasks:task_detail', pk=task_id)
    
    return redirect('tasks:task_detail', pk=task_id)

@login_required
def add_multiple_attachments(request, task_id):
    """Agregar múltiples archivos adjuntos a una tarea."""
    task = get_object_or_404(Task, pk=task_id)
    
    # Verificar permisos
    if not (request.user == task.assigned_to or request.user == task.created_by or request.user.is_superuser):
        return JsonResponse({'error': _('No tienes permisos para agregar archivos a esta tarea.')}, status=403)
    
    if request.method == 'POST':
        form = MultipleTaskAttachmentForm(request.POST, request.FILES, task=task)
        if form.is_valid():
            files = form.cleaned_data['files']
            description = form.cleaned_data.get('description', '')
            group = form.cleaned_data.get('group')
            is_public = form.cleaned_data.get('is_public', False)
            
            if not isinstance(files, list):
                files = [files]
            
            created_attachments = []
            for file in files:
                attachment = TaskAttachment.objects.create(
                    task=task,
                    file=file,
                    description=description,
                    group=group,
                    is_public=is_public,
                    uploaded_by=request.user
                )
                created_attachments.append(attachment)
            
            # Registrar en historial
            TaskHistory.objects.create(
                task=task,
                action='updated',
                user=request.user,
                description=f'{len(created_attachments)} archivos agregados'
            )
            
            messages.success(request, _(f'{len(created_attachments)} archivos agregados exitosamente.'))
            return redirect('tasks:task_detail', pk=task_id)
        else:
            for error in form.non_field_errors():
                messages.error(request, error)
    
    return redirect('tasks:task_detail', pk=task_id)

@login_required
def add_task_image(request, task_id):
    """Agregar imagen a una tarea."""
    task = get_object_or_404(Task, pk=task_id)
    
    # Verificar permisos
    if not (request.user == task.assigned_to or request.user == task.created_by or request.user.is_superuser):
        return JsonResponse({'error': _('No tienes permisos para agregar imágenes a esta tarea.')}, status=403)
    
    if request.method == 'POST':
        form = TaskImageForm(request.POST, request.FILES)
        if form.is_valid():
            image = form.save(commit=False)
            image.task = task
            image.uploaded_by = request.user
            image.save()
            
            # Registrar en historial
            TaskHistory.objects.create(
                task=task,
                action='updated',
                user=request.user,
                description=f'Imagen agregada: {image.title or "Sin título"}'
            )
            
            messages.success(request, _('Imagen agregada exitosamente.'))
            return redirect('tasks:task_detail', pk=task_id)
    
    return redirect('tasks:task_detail', pk=task_id)

@login_required
def add_multiple_images(request, task_id):
    """Agregar múltiples imágenes a una tarea."""
    task = get_object_or_404(Task, pk=task_id)
    
    # Verificar permisos
    if not (request.user == task.assigned_to or request.user == task.created_by or request.user.is_superuser):
        return JsonResponse({'error': _('No tienes permisos para agregar imágenes a esta tarea.')}, status=403)
    
    if request.method == 'POST':
        form = MultipleTaskImageForm(request.POST, request.FILES)
        if form.is_valid():
            images = form.cleaned_data['images']
            title_prefix = form.cleaned_data.get('title_prefix', '')
            description = form.cleaned_data.get('description', '')
            location = form.cleaned_data.get('location', '')
            is_public = form.cleaned_data.get('is_public', False)
            
            if not isinstance(images, list):
                images = [images]
            
            created_images = []
            for i, image in enumerate(images, 1):
                # Generar título automático si hay prefijo
                auto_title = f"{title_prefix}{i}" if title_prefix else f"Imagen {i}"
                
                task_image = TaskImage.objects.create(
                    task=task,
                    image=image,
                    title=auto_title,
                    description=description,
                    location=location,
                    is_public=is_public,
                    uploaded_by=request.user
                )
                created_images.append(task_image)
            
            # Registrar en historial
            TaskHistory.objects.create(
                task=task,
                action='updated',
                user=request.user,
                description=f'{len(created_images)} imágenes agregadas'
            )
            
            messages.success(request, _(f'{len(created_images)} imágenes agregadas exitosamente.'))
            return redirect('tasks:task_detail', pk=task_id)
        else:
            for error in form.non_field_errors():
                messages.error(request, error)
    
    return redirect('tasks:task_detail', pk=task_id)

@login_required
def create_attachment_group(request, task_id):
    """Crear grupo de archivos adjuntos."""
    task = get_object_or_404(Task, pk=task_id)
    
    # Verificar permisos
    if not (request.user == task.assigned_to or request.user == task.created_by or request.user.is_superuser):
        return JsonResponse({'error': _('No tienes permisos para crear grupos en esta tarea.')}, status=403)
    
    if request.method == 'POST':
        form = TaskAttachmentGroupForm(request.POST)
        if form.is_valid():
            group = form.save(commit=False)
            group.task = task
            group.created_by = request.user
            group.save()
            
            messages.success(request, _('Grupo de archivos creado exitosamente.'))
            return redirect('tasks:task_detail', pk=task_id)
    
    return redirect('tasks:task_detail', pk=task_id)

@login_required
def delete_attachment(request, task_id, attachment_id):
    """Eliminar archivo adjunto."""
    task = get_object_or_404(Task, pk=task_id)
    attachment = get_object_or_404(TaskAttachment, pk=attachment_id, task=task)
    
    # Verificar permisos
    if not (request.user == task.assigned_to or request.user == task.created_by or 
            request.user == attachment.uploaded_by or request.user.is_superuser):
        return JsonResponse({'error': _('No tienes permisos para eliminar este archivo.')}, status=403)
    
    if request.method == 'POST':
        file_name = attachment.original_name
        attachment.delete()
        
        # Registrar en historial
        TaskHistory.objects.create(
            task=task,
            action='updated',
            user=request.user,
            description=f'Archivo eliminado: {file_name}'
        )
        
        messages.success(request, _('Archivo eliminado exitosamente.'))
    
    return redirect('tasks:task_detail', pk=task_id)

@login_required
def delete_image(request, task_id, image_id):
    """Eliminar imagen."""
    task = get_object_or_404(Task, pk=task_id)
    image = get_object_or_404(TaskImage, pk=image_id, task=task)
    
    # Verificar permisos
    if not (request.user == task.assigned_to or request.user == task.created_by or 
            request.user == image.uploaded_by or request.user.is_superuser):
        return JsonResponse({'error': _('No tienes permisos para eliminar esta imagen.')}, status=403)
    
    if request.method == 'POST':
        image_title = image.title or 'Imagen sin título'
        image.delete()
        
        # Registrar en historial
        TaskHistory.objects.create(
            task=task,
            action='updated',
            user=request.user,
            description=f'Imagen eliminada: {image_title}'
        )
        
        messages.success(request, _('Imagen eliminada exitosamente.'))
    
    return redirect('tasks:task_detail', pk=task_id)

@login_required
def set_primary_image(request, task_id, image_id):
    """Establecer imagen como principal."""
    task = get_object_or_404(Task, pk=task_id)
    image = get_object_or_404(TaskImage, pk=image_id, task=task)
    
    # Verificar permisos
    if not (request.user == task.assigned_to or request.user == task.created_by or request.user.is_superuser):
        return JsonResponse({'error': _('No tienes permisos para modificar esta tarea.')}, status=403)
    
    if request.method == 'POST':
        # Desmarcar otras imágenes principales
        TaskImage.objects.filter(task=task, is_primary=True).update(is_primary=False)
        
        # Marcar esta imagen como principal
        image.is_primary = True
        image.save()
        
        messages.success(request, _('Imagen establecida como principal.'))
    
    return redirect('tasks:task_detail', pk=task_id)

@login_required
def quick_create_task(request):
    """Vista para crear tarea rápida via AJAX."""
    if not user_has_tasks_permission(request.user, 'add'):
        return JsonResponse({'error': _('No tienes permisos para crear tareas.')}, status=403)
    
    if request.method == 'POST':
        form = TaskQuickCreateForm(request.POST, user=request.user)
        if form.is_valid():
            task = form.save(commit=False)
            task.created_by = request.user
            task.save()
            
            # Registrar en historial
            TaskHistory.objects.create(
                task=task,
                action='created',
                user=request.user,
                description=f'Tarea rápida creada y asignada a {task.assigned_to.get_full_name_display()}'
            )
            
            return JsonResponse({
                'success': True,
                'message': _('Tarea creada exitosamente.'),
                'task_id': task.id,
                'task_url': reverse('tasks:task_detail', kwargs={'pk': task.id})
            })
        else:
            return JsonResponse({'success': False, 'errors': form.errors})
    
    return JsonResponse({'error': _('Método no permitido.')}, status=405)

# VISTAS PARA CATEGORÍAS

class TaskCategoryListView(LoginRequiredMixin, TaskPermissionMixin, ListView):
    """Vista para listar categorías de tareas."""
    model = TaskCategory
    template_name = 'tasks/category_list.html'
    context_object_name = 'categories'
    permission_action = 'view'
    
    def get_queryset(self):
        return TaskCategory.objects.annotate(
            task_count=Count('task')
        ).order_by('module', 'name')

class TaskCategoryCreateView(LoginRequiredMixin, TaskPermissionMixin, CreateView):
    """Vista para crear categorías de tareas."""
    model = TaskCategory
    form_class = TaskCategoryForm
    template_name = 'tasks/category_form.html'
    success_url = reverse_lazy('tasks:category_list')
    permission_action = 'add'
    
    def form_valid(self, form):
        messages.success(self.request, _('Categoría creada exitosamente.'))
        return super().form_valid(form)

class TaskCategoryUpdateView(LoginRequiredMixin, TaskPermissionMixin, UpdateView):
    """Vista para actualizar categorías de tareas."""
    model = TaskCategory
    form_class = TaskCategoryForm
    template_name = 'tasks/category_form.html'
    success_url = reverse_lazy('tasks:category_list')
    permission_action = 'change'
    
    def form_valid(self, form):
        messages.success(self.request, _('Categoría actualizada exitosamente.'))
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['editing'] = True
        return context

class TaskCategoryDeleteView(LoginRequiredMixin, TaskPermissionMixin, DeleteView):
    """Vista para eliminar categorías de tareas."""
    model = TaskCategory
    template_name = 'tasks/category_confirm_delete.html'
    success_url = reverse_lazy('tasks:category_list')
    permission_action = 'delete'
    
    def delete(self, request, *args, **kwargs):
        category = self.get_object()
        messages.success(request, f'Categoría "{category.name}" eliminada exitosamente.')
        return super().delete(request, *args, **kwargs)

@login_required
def tasks_cost_center_report(request):
    """Vista para reportes por centro de costos."""
    if not user_has_tasks_permission(request.user, 'view'):
        return HttpResponseForbidden(_('No tienes permisos para ver reportes.'))
    
    # Obtener todas las tareas
    tasks = Task.objects.select_related('assigned_to', 'proyecto_relacionado')
    
    # Agrupar por centro de costos
    cost_centers = {}
    
    for task in tasks:
        centro_costos = task.get_centro_costos_display() or 'Sin Centro de Costos'
        
        if centro_costos not in cost_centers:
            cost_centers[centro_costos] = {
                'name': centro_costos,
                'total': 0,
                'pending': 0,
                'in_progress': 0,
                'completed': 0,
                'overdue': 0,
                'high_priority': 0,
                'tasks': []
            }
        
        cost_centers[centro_costos]['total'] += 1
        cost_centers[centro_costos]['tasks'].append(task)
        
        # Contadores por estado
        if task.status == 'pending':
            cost_centers[centro_costos]['pending'] += 1
        elif task.status == 'in_progress':
            cost_centers[centro_costos]['in_progress'] += 1
        elif task.status == 'completed':
            cost_centers[centro_costos]['completed'] += 1
        
        # Tareas vencidas
        if task.is_overdue:
            cost_centers[centro_costos]['overdue'] += 1
        
        # Alta prioridad
        if task.priority in ['high', 'urgent']:
            cost_centers[centro_costos]['high_priority'] += 1
    
    # Convertir a lista y ordenar
    cost_centers_list = list(cost_centers.values())
    cost_centers_list.sort(key=lambda x: x['total'], reverse=True)
    
    context = {
        'cost_centers': cost_centers_list,
        'total_tasks': tasks.count(),
        'total_cost_centers': len(cost_centers_list)
    }
    
    return render(request, 'tasks/cost_center_report.html', context)

@login_required
def get_proyecto_centro_costos(request):
    """Vista AJAX para obtener el centro de costos de un proyecto."""
    proyecto_id = request.GET.get('proyecto_id')
    
    if not proyecto_id:
        return JsonResponse({'error': 'No se proporcionó ID del proyecto'}, status=400)
    
    try:
        # Importar aquí para evitar imports circulares
        from proyectos.models import Proyecto
        proyecto = get_object_or_404(Proyecto, id=proyecto_id)
        
        return JsonResponse({
            'centro_costos': proyecto.centro_costos or '',
            'proyecto_nombre': proyecto.nombre_proyecto
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def get_centro_costos_related_items(request):
    """Vista AJAX para obtener proyectos, servicios y contratos relacionados con un centro de costos."""
    centro_costos = request.GET.get('centro_costos')
    
    if not centro_costos:
        return JsonResponse({'error': 'No se proporcionó centro de costos'}, status=400)
    
    try:
        data = {
            'proyectos': [],
            'servicios': [],
            'mantenimiento': []
        }
        
        # Obtener proyectos relacionados
        try:
            from proyectos.models import Proyecto
            proyectos = Proyecto.objects.filter(
                centro_costos=centro_costos,
                estado__in=['pendiente', 'en_ejecucion']
            ).values('id', 'nombre_proyecto', 'orden_contrato', 'estado').order_by('-estado', '-fecha_inicio')
            data['proyectos'] = list(proyectos)
        except ImportError:
            pass
        
        # Obtener servicios relacionados
        try:
            from servicios.models import SolicitudServicio
            servicios = SolicitudServicio.objects.filter(
                centro_costo=centro_costos
            ).exclude(
                estado__in=['cancelada', 'completada']
            ).values('id', 'nombre_proyecto', 'numero_orden')
            data['servicios'] = list(servicios)
        except ImportError:
            pass
        
        # Obtener contratos de mantenimiento relacionados
        try:
            from mantenimiento.models import ContratoMantenimiento
            # Buscar por centro_costos a través del trato_origen
            contratos = ContratoMantenimiento.objects.filter(
                trato_origen__centro_costos=centro_costos
            ).filter(
                estado='activo'
            ).values('id', 'nombre_contrato', 'numero_contrato')
            data['mantenimiento'] = list(contratos)
        except (ImportError, AttributeError):
            pass
        
        return JsonResponse(data)
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
