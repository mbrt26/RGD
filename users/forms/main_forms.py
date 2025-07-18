from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth.password_validation import validate_password
from django.utils.translation import gettext_lazy as _
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit, Button
from crispy_forms.bootstrap import FormActions
from ..models import User, Role, Permission

class CustomUserCreationForm(UserCreationForm):
    """Formulario para crear usuarios con campos adicionales."""
    
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'telefono', 'cargo', 'role')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('username', css_class='form-group col-md-6 mb-0'),
                Column('email', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('first_name', css_class='form-group col-md-6 mb-0'),
                Column('last_name', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('telefono', css_class='form-group col-md-6 mb-0'),
                Column('cargo', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            'role',
            Row(
                Column('password1', css_class='form-group col-md-6 mb-0'),
                Column('password2', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            FormActions(
                Submit('submit', _('Crear Usuario'), css_class='btn btn-primary'),
                Button('cancel', _('Cancelar'), css_class='btn btn-secondary', 
                      onclick="window.history.back();")
            )
        )

class CustomUserChangeForm(UserChangeForm):
    """Formulario para editar usuarios."""
    
    password = None  # Removemos el campo de contraseña heredado
    new_password1 = forms.CharField(
        label=_("Nueva contraseña"),
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=False,
        help_text=_("Deje en blanco si no desea cambiar la contraseña.")
    )
    new_password2 = forms.CharField(
        label=_("Confirmar nueva contraseña"),
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=False
    )
    
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'telefono', 'cargo', 'role', 'is_active')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('username', css_class='form-group col-md-6 mb-0'),
                Column('email', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('first_name', css_class='form-group col-md-6 mb-0'),
                Column('last_name', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('telefono', css_class='form-group col-md-6 mb-0'),
                Column('cargo', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('role', css_class='form-group col-md-6 mb-0'),
                Column('is_active', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('new_password1', css_class='form-group col-md-6 mb-0'),
                Column('new_password2', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            FormActions(
                Submit('submit', _('Actualizar Usuario'), css_class='btn btn-primary'),
                Button('cancel', _('Cancelar'), css_class='btn btn-secondary', 
                      onclick="window.history.back();")
            )
        )
    
    def clean_new_password1(self):
        password1 = self.cleaned_data.get('new_password1')
        if password1:
            try:
                validate_password(password1, self.instance)
            except forms.ValidationError as error:
                raise forms.ValidationError(error)
        return password1
    
    def clean_new_password2(self):
        password1 = self.cleaned_data.get('new_password1')
        password2 = self.cleaned_data.get('new_password2')
        if password1 and password2:
            if password1 != password2:
                raise forms.ValidationError(_("Las contraseñas no coinciden."))
        return password2
    
    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get('new_password1')
        if password:
            user.set_password(password)
        if commit:
            user.save()
        return user

class RoleForm(forms.ModelForm):
    """Formulario para crear y editar roles."""
    
    class Meta:
        model = Role
        fields = ('name', 'description', 'is_active')
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            'name',
            'description',
            'is_active',
            FormActions(
                Submit('submit', _('Guardar Rol'), css_class='btn btn-primary'),
                Button('cancel', _('Cancelar'), css_class='btn btn-secondary', 
                      onclick="window.history.back();")
            )
        )

class PermissionFormSet(forms.BaseInlineFormSet):
    """FormSet personalizado para permisos."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Crear permisos base para todos los módulos y acciones si no existen
        if not self.instance.pk:
            return
            
        modules = dict(Permission.MODULE_CHOICES)
        actions = dict(Permission.ACTION_CHOICES)
        
        existing_perms = set(
            (perm.module, perm.action) 
            for perm in self.instance.permissions.all()
        )
        
        # Crear permisos faltantes
        for module_key in modules.keys():
            for action_key in actions.keys():
                if (module_key, action_key) not in existing_perms:
                    Permission.objects.create(
                        role=self.instance,
                        module=module_key,
                        action=action_key,
                        is_granted=False
                    )

PermissionInlineFormSet = forms.inlineformset_factory(
    Role, 
    Permission,
    fields=('module', 'action', 'is_granted'),
    formset=PermissionFormSet,
    extra=0,
    can_delete=False
)

class RoleWithPermissionsForm(forms.ModelForm):
    """Formulario combinado para rol con permisos."""
    
    class Meta:
        model = Role
        fields = ('name', 'description', 'is_active')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Row(
                Column('name', css_class='form-group col-md-8 mb-0'),
                Column('is_active', css_class='form-group col-md-4 mb-0'),
                css_class='form-row'
            ),
            'description',
        )

class BulkPermissionForm(forms.Form):
    """Formulario para asignar permisos en masa a un rol."""
    
    def __init__(self, role=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.role = role
        
        if role:
            modules = dict(Permission.MODULE_CHOICES)
            actions = dict(Permission.ACTION_CHOICES)
            
            for module_key, module_name in modules.items():
                for action_key, action_name in actions.items():
                    field_name = f"{module_key}_{action_key}"
                    try:
                        permission = Permission.objects.get(
                            role=role, module=module_key, action=action_key
                        )
                        initial_value = permission.is_granted
                    except Permission.DoesNotExist:
                        initial_value = False
                    
                    self.fields[field_name] = forms.BooleanField(
                        label=f"{module_name} - {action_name}",
                        required=False,
                        initial=initial_value
                    )
        
        self.helper = FormHelper()
        self.helper.form_tag = False
    
    def save(self):
        """Guarda los permisos modificados."""
        if not self.role:
            return
            
        modules = dict(Permission.MODULE_CHOICES)
        actions = dict(Permission.ACTION_CHOICES)
        
        for module_key in modules.keys():
            for action_key in actions.keys():
                field_name = f"{module_key}_{action_key}"
                is_granted = self.cleaned_data.get(field_name, False)
                
                permission, created = Permission.objects.get_or_create(
                    role=self.role,
                    module=module_key,
                    action=action_key,
                    defaults={'is_granted': is_granted}
                )
                
                if not created:
                    permission.is_granted = is_granted
                    permission.save()