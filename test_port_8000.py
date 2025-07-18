#!/usr/bin/env python
import os
import sys
sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rgd_aire.settings_dev')

import django
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model

# Test complete flow on port 8000
client = Client()

# Login
User = get_user_model()
user = User.objects.get(username='demo')
client.force_login(user)

# Test URLs
print("Testing URLs on port 8000:")
print("=" * 40)

# Test projects
response = client.get('/proyectos/proyectos/')
print(f"Projects: {response.status_code} - {'✅ OK' if response.status_code == 200 else '❌ Error'}")

# Test services
response = client.get('/servicios/solicitudes/')
print(f"Services: {response.status_code} - {'✅ OK' if response.status_code == 200 else '❌ Error'}")

# Test root
response = client.get('/')
print(f"Root: {response.status_code} - {'✅ OK' if response.status_code in [200, 302] else '❌ Error'}")

print("\n🌐 Access URLs:")
print("Login: http://localhost:8000/users/login/")
print("Projects: http://localhost:8000/proyectos/proyectos/")
print("Services: http://localhost:8000/servicios/solicitudes/")
print("\n👤 Credentials:")
print("Username: demo")
print("Password: demo123")