from django.contrib.auth.views import LoginView, LogoutView, PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, DetailView, UpdateView, DeleteView
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse, HttpResponse
from django.template.loader import render_to_string
import pandas as pd
import io
from django.db import transaction
from .models import User, Role, Permission
from .forms import (
    CustomUserCreationForm, CustomUserChangeForm, RoleForm, 
    PermissionInlineFormSet, RoleWithPermissionsForm, BulkPermissionForm
)

def user_has_users_permission(user, action='view'):
    """Verifica si el usuario tiene permisos en el módulo de usuarios."""
    if not user.is_authenticated:
        return False
    return user.is_superuser or user.has_module_permission('users', action)

class UserPermissionMixin(UserPassesTestMixin):
    """Mixin para verificar permisos de usuarios."""
    permission_action = 'view'
    
    def test_func(self):
        return user_has_users_permission(self.request.user, self.permission_action)

class SignUpView(CreateView):
    form_class = UserCreationForm
    success_url = reverse_lazy('users:login')
    template_name = 'registration/signup.html'
    
    def form_valid(self, form):
        messages.success(self.request, _('Account created successfully! Please log in.'))
        return super().form_valid(form)

class CustomLoginView(LoginView):
    template_name = 'registration/login.html'
    redirect_authenticated_user = True
    success_url = reverse_lazy('crm:dashboard')
    
    def get_success_url(self):
        """
        Return the user-originating redirect URL if it's safe.
        """
        redirect_to = self.request.POST.get(
            self.redirect_field_name,
            self.request.GET.get(self.redirect_field_name, '')
        )
        if redirect_to:
            return redirect_to
        return reverse_lazy('crm:dashboard')
    
    def form_valid(self, form):
        """Security check complete. Log the user in."""
        messages.success(self.request, _('¡Bienvenido! Has iniciado sesión correctamente.'))
        return super().form_valid(form)

class CustomLogoutView(LogoutView):
    next_page = 'users:login'
    http_method_names = ['get', 'post', 'options']  # Permitir GET además de POST
    
    def get(self, request, *args, **kwargs):
        """Permitir logout con GET request."""
        messages.info(request, _('Has cerrado sesión correctamente.'))
        return self.post(request, *args, **kwargs)
    
    def dispatch(self, request, *args, **kwargs):
        if request.method == 'POST':
            messages.info(request, _('Has cerrado sesión correctamente.'))
        return super().dispatch(request, *args, **kwargs)

# VISTAS PARA GESTIÓN DE USUARIOS

class UserListView(LoginRequiredMixin, UserPermissionMixin, ListView):
    """Vista para listar usuarios."""
    model = User
    template_name = 'users/user_list.html'
    context_object_name = 'users'
    paginate_by = 20
    permission_action = 'view'
    
    def get_queryset(self):
        queryset = User.objects.select_related('role')
        search_query = self.request.GET.get('search')
        
        if search_query:
            queryset = queryset.filter(
                Q(username__icontains=search_query) |
                Q(first_name__icontains=search_query) |
                Q(last_name__icontains=search_query) |
                Q(email__icontains=search_query) |
                Q(cargo__icontains=search_query)
            )
        
        return queryset.order_by('username')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '')
        context['can_add'] = user_has_users_permission(self.request.user, 'add')
        context['can_change'] = user_has_users_permission(self.request.user, 'change')
        context['can_delete'] = user_has_users_permission(self.request.user, 'delete')
        context['can_import'] = user_has_users_permission(self.request.user, 'import')
        return context

class UserDetailView(LoginRequiredMixin, UserPermissionMixin, DetailView):
    """Vista para ver detalles de un usuario."""
    model = User
    template_name = 'users/user_detail.html'
    context_object_name = 'user_obj'
    permission_action = 'view'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['can_change'] = user_has_users_permission(self.request.user, 'change')
        context['can_delete'] = user_has_users_permission(self.request.user, 'delete')
        return context

class UserCreateView(LoginRequiredMixin, UserPermissionMixin, CreateView):
    """Vista para crear usuarios."""
    model = User
    form_class = CustomUserCreationForm
    template_name = 'users/user_form.html'
    success_url = reverse_lazy('users:user_list')
    permission_action = 'add'
    
    def form_valid(self, form):
        messages.success(self.request, _('Usuario creado exitosamente.'))
        return super().form_valid(form)

class UserUpdateView(LoginRequiredMixin, UserPermissionMixin, UpdateView):
    """Vista para editar usuarios."""
    model = User
    form_class = CustomUserChangeForm
    template_name = 'users/user_form.html'
    success_url = reverse_lazy('users:user_list')
    permission_action = 'change'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['editing'] = True
        return context
    
    def form_valid(self, form):
        messages.success(self.request, _('Usuario actualizado exitosamente.'))
        return super().form_valid(form)

class UserDeleteView(LoginRequiredMixin, UserPermissionMixin, DeleteView):
    """Vista para eliminar usuarios."""
    model = User
    template_name = 'users/user_confirm_delete.html'
    success_url = reverse_lazy('users:user_list')
    permission_action = 'delete'
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, _('Usuario eliminado exitosamente.'))
        return super().delete(request, *args, **kwargs)

# VISTAS PARA GESTIÓN DE ROLES

class RoleListView(LoginRequiredMixin, UserPermissionMixin, ListView):
    """Vista para listar roles."""
    model = Role
    template_name = 'users/role_list.html'
    context_object_name = 'roles'
    paginate_by = 20
    permission_action = 'view'
    
    def get_queryset(self):
        queryset = Role.objects.prefetch_related('users', 'permissions')
        search_query = self.request.GET.get('search')
        
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(description__icontains=search_query)
            )
        
        return queryset.order_by('name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '')
        context['can_add'] = user_has_users_permission(self.request.user, 'add')
        context['can_change'] = user_has_users_permission(self.request.user, 'change')
        context['can_delete'] = user_has_users_permission(self.request.user, 'delete')
        context['can_import'] = user_has_users_permission(self.request.user, 'import')
        return context

class RoleDetailView(LoginRequiredMixin, UserPermissionMixin, DetailView):
    """Vista para ver detalles de un rol."""
    model = Role
    template_name = 'users/role_detail.html'
    context_object_name = 'role'
    permission_action = 'view'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['permissions'] = self.object.permissions.all().order_by('module', 'action')
        context['users_count'] = self.object.users.count()
        context['can_change'] = user_has_users_permission(self.request.user, 'change')
        context['can_delete'] = user_has_users_permission(self.request.user, 'delete')
        return context

class RoleCreateView(LoginRequiredMixin, UserPermissionMixin, CreateView):
    """Vista para crear roles."""
    model = Role
    form_class = RoleForm
    template_name = 'users/role_form.html'
    success_url = reverse_lazy('users:role_list')
    permission_action = 'add'
    
    def form_valid(self, form):
        messages.success(self.request, _('Rol creado exitosamente.'))
        return super().form_valid(form)

class RoleUpdateView(LoginRequiredMixin, UserPermissionMixin, UpdateView):
    """Vista para editar roles."""
    model = Role
    form_class = RoleForm
    template_name = 'users/role_form.html'
    success_url = reverse_lazy('users:role_list')
    permission_action = 'change'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['editing'] = True
        return context
    
    def form_valid(self, form):
        messages.success(self.request, _('Rol actualizado exitosamente.'))
        return super().form_valid(form)

class RoleDeleteView(LoginRequiredMixin, UserPermissionMixin, DeleteView):
    """Vista para eliminar roles."""
    model = Role
    template_name = 'users/role_confirm_delete.html'
    success_url = reverse_lazy('users:role_list')
    permission_action = 'delete'
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, _('Rol eliminado exitosamente.'))
        return super().delete(request, *args, **kwargs)

@login_required
def role_permissions_view(request, pk):
    """Vista para gestionar permisos de un rol."""
    if not user_has_users_permission(request.user, 'change'):
        messages.error(request, _('No tienes permisos para realizar esta acción.'))
        return redirect('users:role_list')
    
    role = get_object_or_404(Role, pk=pk)
    
    if request.method == 'POST':
        form = BulkPermissionForm(role=role, data=request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, _('Permisos actualizados exitosamente.'))
            return redirect('users:role_detail', pk=role.pk)
    else:
        form = BulkPermissionForm(role=role)
    
    # Organizar permisos por módulo
    modules = dict(Permission.MODULE_CHOICES)
    actions = dict(Permission.ACTION_CHOICES)
    
    permissions_by_module = {}
    for module_key, module_name in modules.items():
        permissions_by_module[module_name] = []
        for action_key, action_name in actions.items():
            field_name = f"{module_key}_{action_key}"
            field = form.fields.get(field_name)
            if field:
                permissions_by_module[module_name].append({
                    'field': form[field_name],
                    'action': action_name,
                    'module_key': module_key,
                    'action_key': action_key,
                })
    
    return render(request, 'users/role_permissions.html', {
        'role': role,
        'form': form,
        'permissions_by_module': permissions_by_module,
    })

@login_required
def users_dashboard(request):
    """Dashboard para gestión de usuarios y roles."""
    if not user_has_users_permission(request.user, 'view'):
        messages.error(request, _('No tienes permisos para acceder a esta sección.'))
        return redirect('crm:dashboard')
    
    context = {
        'users_count': User.objects.count(),
        'active_users_count': User.objects.filter(is_active=True).count(),
        'roles_count': Role.objects.count(),
        'active_roles_count': Role.objects.filter(is_active=True).count(),
        'recent_users': User.objects.order_by('-created_at')[:5],
        'can_add_user': user_has_users_permission(request.user, 'add'),
        'can_add_role': user_has_users_permission(request.user, 'add'),
    }
    
    return render(request, 'users/dashboard.html', context)

# VISTAS PARA IMPORTACIÓN DE EXCEL

@login_required
def users_import_template(request):
    """Genera y descarga plantilla Excel para importar usuarios."""
    if not user_has_users_permission(request.user, 'import'):
        messages.error(request, _('No tienes permisos para realizar esta acción.'))
        return redirect('users:user_list')
    
    # Crear DataFrame con columnas de ejemplo
    template_data = {
        'username': ['usuario1', 'usuario2'],
        'first_name': ['Juan', 'María'],
        'last_name': ['Pérez', 'García'],
        'email': ['juan.perez@empresa.com', 'maria.garcia@empresa.com'],
        'telefono': ['3001234567', '3007654321'],
        'cargo': ['Desarrollador', 'Analista'],
        'role_name': ['Desarrollador', 'Analista'],
        'is_active': [True, True],
        'password': ['temporal123', 'temporal456']
    }
    
    df = pd.DataFrame(template_data)
    
    # Crear buffer de memoria
    buffer = io.BytesIO()
    
    # Escribir Excel con formato
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Usuarios', index=False)
        
        # Obtener el workbook y worksheet
        workbook = writer.book
        worksheet = writer.sheets['Usuarios']
        
        # Ajustar ancho de columnas
        for column in worksheet.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            worksheet.column_dimensions[column_letter].width = adjusted_width
    
    buffer.seek(0)
    
    response = HttpResponse(
        buffer.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="plantilla_usuarios.xlsx"'
    
    return response

from django.views.generic import FormView
from django.contrib.auth.mixins import LoginRequiredMixin
from .forms.import_forms import UserImportForm
import logging

logger = logging.getLogger(__name__)

class UserImportView(LoginRequiredMixin, FormView):
    """Vista para importar usuarios desde archivo Excel."""
    template_name = 'users/user_import.html'
    form_class = UserImportForm
    success_url = reverse_lazy('users:user_list')
    
    def dispatch(self, request, *args, **kwargs):
        if not user_has_users_permission(request.user, 'import'):
            messages.error(request, 'No tienes permisos para realizar esta acción.')
            return redirect('users:user_list')
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        try:
            archivo_excel = form.cleaned_data['archivo_excel']
            
            # Inicializar estadísticas de importación
            import_stats = {
                'created': 0,
                'errors': 0,
                'skipped': 0,
                'total_rows': 0,
                'error_details': []
            }
            
            logger.info("Iniciando importación de usuarios desde Excel")
            
            # Leer archivo Excel con manejo de errores
            try:
                df = pd.read_excel(archivo_excel, engine='openpyxl')
                logger.info(f"Archivo Excel leído exitosamente: {len(df)} filas")
            except Exception as excel_error:
                logger.error(f"Error al leer archivo Excel: {str(excel_error)}")
                messages.error(self.request, f'Error al leer archivo Excel: {str(excel_error)}')
                return self.form_invalid(form)
            
            # Verificar que el archivo no esté vacío
            if df.empty:
                messages.error(self.request, 'El archivo Excel está vacío.')
                return self.form_invalid(form)
            
            # Validar columnas requeridas
            required_columns = ['username', 'email', 'first_name', 'last_name']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                error_msg = f'Faltan las siguientes columnas requeridas: {", ".join(missing_columns)}'
                logger.error(error_msg)
                messages.error(self.request, error_msg)
                return self.form_invalid(form)
            
            # Limitar a 500 filas por proceso para evitar timeouts
            max_rows = min(len(df), 500)
            if len(df) > 500:
                logger.warning(f"Archivo tiene {len(df)} filas. Procesando solo las primeras 500 para evitar timeouts.")
                messages.warning(self.request, f"Archivo tiene {len(df)} filas. Procesando solo las primeras 500 por seguridad.")
            
            import_stats['total_rows'] = max_rows
            
            # OPTIMIZACIÓN: Precargar todos los roles y usuarios existentes
            logger.info("Precargando roles y usuarios existentes para optimización...")
            try:
                all_roles = {role.name: role for role in Role.objects.all()}
                existing_usernames = set(User.objects.values_list('username', flat=True))
                existing_emails = set(User.objects.values_list('email', flat=True))
                logger.info(f"Precargados {len(all_roles)} roles, {len(existing_usernames)} usernames, {len(existing_emails)} emails")
            except Exception as e:
                logger.error(f"Error precargando datos: {str(e)}")
                all_roles = {}
                existing_usernames = set()
                existing_emails = set()
            
            # Helper functions para limpieza de datos
            def clean_text_field(value, default=''):
                if pd.isna(value) or value is None:
                    return default
                return str(value).strip()
            
            def clean_boolean_field(value, default=True):
                if pd.isna(value) or value is None:
                    return default
                if isinstance(value, str):
                    return value.lower() in ['true', '1', 'yes', 'sí', 'verdadero']
                return bool(value)
            
            # Preparar datos para bulk insert
            users_to_create = []
            
            logger.info(f"Procesando {max_rows} filas para bulk insert...")
            
            # Procesar cada fila y preparar objetos User
            for index, row in df.head(max_rows).iterrows():
                try:
                    # Validar campos obligatorios
                    username = clean_text_field(row['username'])
                    email = clean_text_field(row['email'])
                    first_name = clean_text_field(row['first_name'])
                    last_name = clean_text_field(row['last_name'])
                    
                    if not username:
                        warning_msg = f'Username vacío en fila {index + 2}. Se omitirá este usuario.'
                        import_stats['skipped'] += 1
                        import_stats['error_details'].append(warning_msg)
                        continue
                    
                    if not email:
                        warning_msg = f'Email vacío en fila {index + 2}. Se omitirá este usuario.'
                        import_stats['skipped'] += 1
                        import_stats['error_details'].append(warning_msg)
                        continue
                    
                    # Verificar duplicados usando datos precargados
                    if username in existing_usernames:
                        warning_msg = f'Username "{username}" ya existe en fila {index + 2}. Se omitirá este usuario.'
                        import_stats['skipped'] += 1
                        import_stats['error_details'].append(warning_msg)
                        continue
                    
                    if email in existing_emails:
                        warning_msg = f'Email "{email}" ya existe en fila {index + 2}. Se omitirá este usuario.'
                        import_stats['skipped'] += 1
                        import_stats['error_details'].append(warning_msg)
                        continue
                    
                    # Buscar rol usando diccionario precargado
                    role = None
                    role_name = clean_text_field(row.get('role_name', ''))
                    if role_name:
                        role = all_roles.get(role_name)
                        if not role:
                            warning_msg = f'Rol "{role_name}" no encontrado en fila {index + 2}. Se asignará sin rol.'
                            import_stats['error_details'].append(warning_msg)
                    
                    # Crear objeto User (sin guardarlo aún)
                    password = clean_text_field(row.get('password', 'temporal123'))
                    user = User(
                        username=username,
                        email=email,
                        first_name=first_name,
                        last_name=last_name,
                        telefono=clean_text_field(row.get('telefono', '')),
                        cargo=clean_text_field(row.get('cargo', '')),
                        role=role,
                        is_active=clean_boolean_field(row.get('is_active', True)),
                    )
                    
                    # Hash de la contraseña
                    user.set_password(password)
                    
                    users_to_create.append(user)
                    
                    # Agregar a conjuntos existentes para evitar duplicados en el mismo archivo
                    existing_usernames.add(username)
                    existing_emails.add(email)
                    
                except Exception as e:
                    error_msg = f'Error procesando fila {index + 2}: {str(e)}'
                    import_stats['errors'] += 1
                    import_stats['error_details'].append(error_msg)
                    logger.error(error_msg)
                    continue
            
            # Bulk create todos los usuarios preparados
            if users_to_create:
                logger.info(f"Creando {len(users_to_create)} usuarios usando bulk_create...")
                try:
                    with transaction.atomic():
                        # Crear en lotes de 100 para mejor performance
                        batch_size = 100
                        for i in range(0, len(users_to_create), batch_size):
                            batch = users_to_create[i:i + batch_size]
                            created_users = User.objects.bulk_create(batch, batch_size=batch_size)
                            import_stats['created'] += len(created_users)
                            logger.info(f"Lote {i//batch_size + 1}: {len(created_users)} usuarios creados")
                        
                        logger.info(f"Bulk create completado: {import_stats['created']} usuarios creados")
                        
                except Exception as e:
                    error_msg = f'Error en bulk_create: {str(e)}'
                    import_stats['errors'] += len(users_to_create)
                    import_stats['error_details'].append(error_msg)
                    logger.error(error_msg)
            else:
                logger.warning("No hay usuarios válidos para crear")
            
            # Log estadísticas finales
            logger.info(f"Importación completada. Estadísticas: {import_stats}")
            
            # Crear mensaje de éxito detallado
            success_message = f'Importación completada: {import_stats["created"]} usuarios creados'
            if import_stats['skipped'] > 0:
                success_message += f', {import_stats["skipped"]} omitidos'
            if import_stats['errors'] > 0:
                success_message += f', {import_stats["errors"]} errores'
            success_message += f' de {import_stats["total_rows"]} filas procesadas.'
            
            messages.success(self.request, success_message)
            
            # Agregar información detallada de errores si los hay
            if import_stats['error_details']:
                error_details = import_stats['error_details'][:10]  # Mostrar solo los primeros 10
                error_message = 'Detalles de problemas encontrados:\n' + '\n'.join(error_details)
                if len(import_stats['error_details']) > 10:
                    error_message += f'\n... y {len(import_stats["error_details"]) - 10} problemas más.'
                messages.warning(self.request, error_message)
            
        except Exception as e:
            error_msg = f'Error general en la importación: {str(e)}'
            logger.error(error_msg)
            messages.error(self.request, error_msg)
            return self.form_invalid(form)
        
        return super().form_valid(form)

# Función legacy para compatibilidad
@login_required
def users_import_excel(request):
    """Función legacy redirigida a la nueva vista basada en clase."""
    return UserImportView.as_view()(request)

@login_required
def roles_import_template(request):
    """Genera y descarga plantilla Excel para importar roles."""
    if not user_has_users_permission(request.user, 'import'):
        messages.error(request, _('No tienes permisos para realizar esta acción.'))
        return redirect('users:role_list')
    
    # Crear DataFrame con columnas de ejemplo
    template_data = {
        'name': ['Desarrollador', 'Analista'],
        'description': ['Rol para desarrolladores del sistema', 'Rol para analistas de datos'],
        'is_active': [True, True]
    }
    
    df = pd.DataFrame(template_data)
    
    # Crear buffer de memoria
    buffer = io.BytesIO()
    
    # Escribir Excel con formato
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Roles', index=False)
        
        # Obtener el workbook y worksheet
        workbook = writer.book
        worksheet = writer.sheets['Roles']
        
        # Ajustar ancho de columnas
        for column in worksheet.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            worksheet.column_dimensions[column_letter].width = adjusted_width
    
    buffer.seek(0)
    
    response = HttpResponse(
        buffer.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="plantilla_roles.xlsx"'
    
    return response

@login_required
def roles_import_excel(request):
    """Importa roles desde archivo Excel."""
    if not user_has_users_permission(request.user, 'import'):
        messages.error(request, _('No tienes permisos para realizar esta acción.'))
        return redirect('users:role_list')
    
    if request.method == 'POST' and request.FILES.get('excel_file'):
        try:
            excel_file = request.FILES['excel_file']
            
            # Leer archivo Excel
            df = pd.read_excel(excel_file)
            
            # Validar columnas requeridas
            required_columns = ['name']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                messages.error(request, _(f'Faltan las siguientes columnas: {", ".join(missing_columns)}'))
                return redirect('users:role_list')
            
            created_count = 0
            error_count = 0
            errors = []
            
            with transaction.atomic():
                for index, row in df.iterrows():
                    try:
                        # Verificar si el rol ya existe
                        if Role.objects.filter(name=row['name']).exists():
                            errors.append(f"Fila {index + 2}: El rol '{row['name']}' ya existe")
                            error_count += 1
                            continue
                        
                        # Crear rol
                        role = Role.objects.create(
                            name=row['name'],
                            description=row.get('description', ''),
                            is_active=row.get('is_active', True)
                        )
                        
                        created_count += 1
                        
                    except Exception as e:
                        errors.append(f"Fila {index + 2}: Error al crear rol - {str(e)}")
                        error_count += 1
            
            # Mostrar resultados
            if created_count > 0:
                messages.success(request, _(f'Se importaron {created_count} roles exitosamente.'))
            
            if error_count > 0:
                error_msg = _(f'Se encontraron {error_count} errores:\n') + '\n'.join(errors[:10])
                if len(errors) > 10:
                    error_msg += f'\n... y {len(errors) - 10} errores más.'
                messages.error(request, error_msg)
            
        except Exception as e:
            messages.error(request, _(f'Error al procesar el archivo: {str(e)}'))
    
    return redirect('users:role_list')