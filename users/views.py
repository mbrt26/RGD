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
from django.http import JsonResponse
from django.template.loader import render_to_string
from .models import User, Role, Permission
from .forms import (
    CustomUserCreationForm, CustomUserChangeForm, RoleForm, 
    PermissionInlineFormSet, RoleWithPermissionsForm, BulkPermissionForm
)

def user_has_users_permission(user, action='view'):
    """Verifica si el usuario tiene permisos en el módulo de usuarios."""
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
    
    def dispatch(self, request, *args, **kwargs):
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