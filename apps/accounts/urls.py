from django.urls import path
from apps.accounts.views import RegisterView, LoginView, LogoutView, ProfileView

urlpatterns = [
    path('auth/register/', RegisterView.as_view(), name='api-register'),
    path('auth/login/', LoginView.as_view(), name='api-login'),
    path('auth/logout/', LogoutView.as_view(), name='api-logout'),
    path('profile/', ProfileView.as_view(), name='api-profile'),
]
