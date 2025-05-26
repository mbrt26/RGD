from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _

class User(AbstractUser):
    """Custom user model that extends the default User model."""
    email = models.EmailField(_('email address'), unique=True)
    
    # Add any additional fields here
    
    def __str__(self):
        return self.username
