from django.urls import path
from . import views

app_name = 'tasks'

urlpatterns = [
    # Dashboard
    path('', views.tasks_dashboard, name='dashboard'),
    
    # Task management URLs
    path('tasks/', views.TaskListView.as_view(), name='task_list'),
    path('tasks/create/', views.TaskCreateView.as_view(), name='task_create'),
    path('tasks/<int:pk>/', views.TaskDetailView.as_view(), name='task_detail'),
    path('tasks/<int:pk>/edit/', views.TaskUpdateView.as_view(), name='task_edit'),
    path('tasks/<int:pk>/delete/', views.TaskDeleteView.as_view(), name='task_delete'),
    
    # Quick create task (AJAX)
    path('tasks/quick-create/', views.quick_create_task, name='task_quick_create'),
    
    # Comments and attachments
    path('tasks/<int:task_id>/comment/', views.add_task_comment, name='add_comment'),
    path('tasks/<int:task_id>/attachment/', views.add_task_attachment, name='add_attachment'),
    path('tasks/<int:task_id>/attachments/multiple/', views.add_multiple_attachments, name='add_multiple_attachments'),
    path('tasks/<int:task_id>/attachment/<int:attachment_id>/delete/', views.delete_attachment, name='delete_attachment'),
    
    # Images
    path('tasks/<int:task_id>/image/', views.add_task_image, name='add_image'),
    path('tasks/<int:task_id>/images/multiple/', views.add_multiple_images, name='add_multiple_images'),
    path('tasks/<int:task_id>/image/<int:image_id>/delete/', views.delete_image, name='delete_image'),
    path('tasks/<int:task_id>/image/<int:image_id>/set-primary/', views.set_primary_image, name='set_primary_image'),
    
    # Attachment groups
    path('tasks/<int:task_id>/groups/create/', views.create_attachment_group, name='create_attachment_group'),
    
    # Category management URLs
    path('categories/', views.TaskCategoryListView.as_view(), name='category_list'),
    path('categories/create/', views.TaskCategoryCreateView.as_view(), name='category_create'),
    path('categories/<int:pk>/edit/', views.TaskCategoryUpdateView.as_view(), name='category_edit'),
    path('categories/<int:pk>/delete/', views.TaskCategoryDeleteView.as_view(), name='category_delete'),
    
    # Reports
    path('reports/cost-centers/', views.tasks_cost_center_report, name='cost_center_report'),
    
    # AJAX endpoints
    path('ajax/get-proyecto-centro-costos/', views.get_proyecto_centro_costos, name='get_proyecto_centro_costos'),
    path('ajax/get-centro-costos-related/', views.get_centro_costos_related_items, name='get_centro_costos_related_items'),
]