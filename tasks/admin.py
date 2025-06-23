from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Task, TaskCategory, TaskComment, TaskAttachment, TaskHistory

class TaskCommentInline(admin.TabularInline):
    """Inline para comentarios de tareas."""
    model = TaskComment
    extra = 0
    fields = ('author', 'content', 'is_internal', 'created_at')
    readonly_fields = ('created_at',)

class TaskAttachmentInline(admin.TabularInline):
    """Inline para archivos adjuntos de tareas."""
    model = TaskAttachment
    extra = 0
    fields = ('file', 'original_name', 'uploaded_by', 'uploaded_at')
    readonly_fields = ('uploaded_at', 'file_size')

class TaskHistoryInline(admin.TabularInline):
    """Inline para historial de tareas."""
    model = TaskHistory
    extra = 0
    fields = ('action', 'user', 'description', 'created_at')
    readonly_fields = ('created_at',)

@admin.register(TaskCategory)
class TaskCategoryAdmin(admin.ModelAdmin):
    """Admin para categorías de tareas."""
    list_display = ('name', 'module', 'color', 'is_active', 'created_at')
    list_filter = ('module', 'is_active', 'created_at')
    search_fields = ('name', 'description')
    ordering = ('module', 'name')
    
    fieldsets = (
        (None, {
            'fields': ('name', 'module', 'description', 'color', 'is_active')
        }),
        (_('Información de Auditoría'), {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_at',)

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    """Admin para tareas."""
    list_display = ('title', 'assigned_to', 'status', 'priority', 'due_date', 'category', 'created_by', 'created_at')
    list_filter = ('status', 'priority', 'task_type', 'category__module', 'category', 'assigned_to', 'created_at', 'due_date')
    search_fields = ('title', 'description', 'assigned_to__username', 'assigned_to__first_name', 'assigned_to__last_name')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    
    fieldsets = (
        (_('Información Básica'), {
            'fields': ('title', 'description', 'category', 'task_type')
        }),
        (_('Asignación'), {
            'fields': ('assigned_to', 'created_by')
        }),
        (_('Estado y Prioridad'), {
            'fields': ('status', 'priority', 'progress_percentage')
        }),
        (_('Fechas'), {
            'fields': ('start_date', 'due_date', 'completed_date', 'reminder_date')
        }),
        (_('Horas'), {
            'fields': ('estimated_hours', 'actual_hours'),
            'classes': ('collapse',)
        }),
        (_('Configuraciones Avanzadas'), {
            'fields': ('is_recurring', 'recurrence_pattern', 'reminder_sent'),
            'classes': ('collapse',)
        }),
        (_('Objeto Relacionado'), {
            'fields': ('content_type', 'object_id'),
            'classes': ('collapse',)
        }),
        (_('Información de Auditoría'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_at', 'updated_at', 'completed_date')
    
    inlines = [TaskCommentInline, TaskAttachmentInline, TaskHistoryInline]
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'assigned_to', 'created_by', 'category', 'content_type'
        )
    
    def save_model(self, request, obj, form, change):
        if not change:  # Si es una nueva tarea
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(TaskComment)
class TaskCommentAdmin(admin.ModelAdmin):
    """Admin para comentarios de tareas."""
    list_display = ('task', 'author', 'content_preview', 'is_internal', 'created_at')
    list_filter = ('is_internal', 'created_at', 'author')
    search_fields = ('task__title', 'content', 'author__username')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = _('Vista previa del contenido')

@admin.register(TaskAttachment)
class TaskAttachmentAdmin(admin.ModelAdmin):
    """Admin para archivos adjuntos de tareas."""
    list_display = ('task', 'original_name', 'uploaded_by', 'file_size_display', 'uploaded_at')
    list_filter = ('uploaded_at', 'uploaded_by')
    search_fields = ('task__title', 'original_name')
    ordering = ('-uploaded_at',)
    date_hierarchy = 'uploaded_at'
    
    def file_size_display(self, obj):
        if obj.file_size:
            if obj.file_size > 1024*1024:
                return f"{obj.file_size / (1024*1024):.1f} MB"
            elif obj.file_size > 1024:
                return f"{obj.file_size / 1024:.1f} KB"
            else:
                return f"{obj.file_size} bytes"
        return "-"
    file_size_display.short_description = _('Tamaño del archivo')

@admin.register(TaskHistory)
class TaskHistoryAdmin(admin.ModelAdmin):
    """Admin para historial de tareas."""
    list_display = ('task', 'action', 'user', 'description', 'created_at')
    list_filter = ('action', 'created_at', 'user')
    search_fields = ('task__title', 'description', 'user__username')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at',)
