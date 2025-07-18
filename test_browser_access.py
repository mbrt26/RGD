#!/usr/bin/env python
import os
import sys
sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rgd_aire.settings_dev')

import django
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model

# Test browser-like access
client = Client()

# First, get the login page to get CSRF token
print("1. Getting login page...")
response = client.get('/users/login/')
print(f'   Status: {response.status_code}')

# Extract CSRF token
csrf_token = None
if 'csrfmiddlewaretoken' in response.content.decode():
    import re
    match = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', response.content.decode())
    if match:
        csrf_token = match.group(1)
        print(f'   CSRF token found: {csrf_token[:20]}...')

# Now login with proper CSRF token
print("2. Logging in with CSRF token...")
login_data = {
    'username': 'demo',
    'password': 'demo123',
    'csrfmiddlewaretoken': csrf_token
}
response = client.post('/users/login/', login_data)
print(f'   Login status: {response.status_code}')
print(f'   Redirect: {response.get("Location", "No redirect")}')

# Now try accessing projects
print("3. Accessing projects page...")
response = client.get('/proyectos/proyectos/')
print(f'   Projects status: {response.status_code}')

if response.status_code == 200:
    print("   ✅ SUCCESS: Projects page loads correctly!")
    print(f'   Content length: {len(response.content)} bytes')
    
    # Check if delete buttons are present
    content = response.content.decode()
    if 'btn-danger' in content and 'trash' in content:
        print("   ✅ Delete buttons are present in the page")
    else:
        print("   ⚠️ Delete buttons not found in the page")
        
elif response.status_code == 302:
    print(f"   ⚠️ Redirected to: {response.get('Location', 'Unknown')}")
else:
    print(f"   ❌ Error: Status {response.status_code}")
    
# Test services too
print("4. Testing services page...")
response = client.get('/servicios/solicitudes/')
print(f'   Services status: {response.status_code}')

if response.status_code == 200:
    print("   ✅ Services page loads correctly!")