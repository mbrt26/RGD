#!/usr/bin/env python
import os
import sys
sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rgd_aire.settings_dev')

import django
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model

# Test complete login flow
client = Client()

# 1. Check if login page loads
print("1. Testing login page...")
response = client.get('/users/login/')
print(f'   Login page status: {response.status_code}')

# 2. Perform login
print("2. Testing login...")
response = client.post('/users/login/', {
    'username': 'demo',
    'password': 'demo123'
})
print(f'   Login response status: {response.status_code}')
print(f'   Login redirect location: {response.get("Location", "No redirect")}')

# 3. Check if authenticated
print("3. Testing authentication...")
User = get_user_model()
user = User.objects.get(username='demo')
client.force_login(user)
print(f'   User authenticated: {user.is_authenticated}')

# 4. Test projects URL
print("4. Testing projects URL...")
response = client.get('/proyectos/proyectos/')
print(f'   Projects page status: {response.status_code}')

# 5. Test services URL
print("5. Testing services URL...")
response = client.get('/servicios/solicitudes/')
print(f'   Services page status: {response.status_code}')

print("\nAll tests completed!")