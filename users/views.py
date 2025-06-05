from django.contrib.auth.views import LoginView, LogoutView, PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView
from django.urls import reverse_lazy
from django.views.generic import CreateView
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.shortcuts import redirect

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
