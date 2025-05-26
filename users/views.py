from django.contrib.auth.views import LoginView, LogoutView, PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView
from django.urls import reverse_lazy
from django.views.generic import CreateView
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.utils.translation import gettext_lazy as _

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

class CustomLogoutView(LogoutView):
    next_page = 'users:login'
