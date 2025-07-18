#!/usr/bin/env python
import os
import sys

# Add the project directory to Python path
sys.path.insert(0, '/app')

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rgd_aire.settings_dev')

import django
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model

User = get_user_model()
client = Client()
user = User.objects.get(username='demo')
client.force_login(user)

try:
    response = client.get('/proyectos/proyectos/')
    print(f'Status code: {response.status_code}')
    
    if response.status_code == 500:
        print('Server error - there\'s an exception in the view')
    elif response.status_code != 200:
        print('Non-200 response')
    else:
        print('Projects list loads successfully')
        print(f'Response length: {len(response.content)} bytes')
        
except Exception as e:
    print(f'Exception occurred: {e}')
    import traceback
    traceback.print_exc()