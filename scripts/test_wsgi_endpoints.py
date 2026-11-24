import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User

client = Client()

# Test public endpoints
public_endpoints = [
    ('/', 'Landing Page'),
    ('/login/', 'Login Page'),
    ('/register/', 'Register Page'),
    ('/api/v1/opportunities/', 'Opportunities API'),
    ('/api/v1/evaluations/latest/', 'Evaluations API'),
]

print("--- Testing Public Endpoints ---")
for url, name in public_endpoints:
    resp = client.get(url)
    status = resp.status_code
    print(f"[{'PASS' if status == 200 else 'FAIL'}] {name} ({url}) -> Status: {status}")
    assert status == 200, f"Failed on {url}"

# Test authenticated dashboard pages
user, _ = User.objects.get_or_create(username='verify_user_a')
client.force_login(user)

auth_endpoints = [
    ('/dashboard/', 'Dashboard'),
    ('/profile/', 'Profile Page'),
    ('/resume/', 'Resume Page'),
    ('/agent/', 'AI Agent Page'),
    ('/opportunities/', 'Opportunities Page'),
    ('/recommendations/', 'Recommendations Page'),
    ('/compare/', 'Comparison Page'),
    ('/skill-gaps/', 'Skill Gaps Page'),
    ('/saved/', 'Saved Page'),
    ('/preferences/', 'Preferences Page'),
    ('/evaluations/', 'Evaluations Dashboard Page'),
]

print("\n--- Testing Authenticated Dashboard Pages ---")
for url, name in auth_endpoints:
    resp = client.get(url)
    status = resp.status_code
    print(f"[{'PASS' if status == 200 else 'FAIL'}] {name} ({url}) -> Status: {status}")
    assert status == 200, f"Failed on {url}"

print("\nALL 16 WEB & API ENDPOINTS RETURN STATUS 200 OK WITH NO TEMPLATE OR BACKEND ERRORS.")
