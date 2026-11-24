import pytest
from django.contrib.auth.models import User
from django.test import Client
from apps.profiles.models import UserProfile


@pytest.mark.django_db
class TestAuthenticationAndProfiles:
    def test_user_registration(self):
        client = Client()
        response = client.post('/api/v1/auth/register/', {
            'username': 'candidate_test',
            'email': 'candidate@test.com',
            'password': 'StrongPassword123!',
            'full_name': 'Candidate Tester',
            'current_location': 'Bangalore'
        }, content_type='application/json')

        assert response.status_code == 201
        assert User.objects.filter(username='candidate_test').exists()
        user = User.objects.get(username='candidate_test')
        assert hasattr(user, 'profile')
        assert user.profile.current_location == 'Bangalore'

    def test_user_login_success(self):
        user = User.objects.create_user(username='login_user', password='Password123!')
        UserProfile.objects.create(user=user)

        client = Client()
        response = client.post('/api/v1/auth/login/', {
            'username': 'login_user',
            'password': 'Password123!'
        }, content_type='application/json')

        assert response.status_code == 200
        assert response.json()['status'] == 'success'

    def test_user_login_invalid_credentials(self):
        client = Client()
        response = client.post('/api/v1/auth/login/', {
            'username': 'nonexistent_user',
            'password': 'WrongPassword'
        }, content_type='application/json')

        assert response.status_code == 401

    def test_unauthenticated_profile_access_denied(self):
        client = Client()
        response = client.get('/api/v1/profile/')
        assert response.status_code in (401, 403)

    def test_profile_update(self):
        user = User.objects.create_user(username='profile_user', password='Password123!')
        profile = UserProfile.objects.create(user=user, headline='Junior Dev')

        client = Client()
        client.force_login(user)

        response = client.put('/api/v1/profile/', {
            'headline': 'Senior Backend Engineer',
            'experience_months': 24,
            'willing_to_relocate': True
        }, content_type='application/json')

        assert response.status_code == 200
        profile.refresh_from_db()
        assert profile.headline == 'Senior Backend Engineer'
        assert profile.experience_months == 24
