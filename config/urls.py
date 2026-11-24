"""
MatchForge URL Configuration.
Exposes domain web pages and REST API v1 endpoints.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from config.web_views import (
    landing_page, register_page, login_page, logout_action,
    dashboard_view, profile_view, resume_upload_view, chat_agent_view,
    opportunities_discovery_view, recommendations_view, opportunity_detail_view,
    compare_view, skill_gaps_view, saved_opportunities_view,
    preferences_management_view, evaluations_dashboard_view
)

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # Web Pages (Server-Rendered UI)
    path('', landing_page, name='landing'),
    path('register/', register_page, name='register'),
    path('login/', login_page, name='login'),
    path('logout/', logout_action, name='logout'),
    
    # Authenticated SaaS Dashboard Pages
    path('dashboard/', dashboard_view, name='dashboard'),
    path('profile/', profile_view, name='profile'),
    path('resume/', resume_upload_view, name='resume'),
    path('agent/', chat_agent_view, name='chat-agent'),
    path('opportunities/', opportunities_discovery_view, name='opportunities'),
    path('opportunities/<uuid:id>/', opportunity_detail_view, name='opportunity-detail'),
    path('recommendations/', recommendations_view, name='recommendations'),
    path('compare/', compare_view, name='compare'),
    path('skill-gaps/', skill_gaps_view, name='skill-gaps'),
    path('saved/', saved_opportunities_view, name='saved'),
    path('preferences/', preferences_management_view, name='preferences-ui'),
    path('evaluations/', evaluations_dashboard_view, name='evaluations-ui'),

    # REST API v1 Routing
    path('api/v1/', include('apps.accounts.urls')),
    path('api/v1/', include('apps.resumes.urls')),
    path('api/v1/', include('apps.preferences.urls')),
    path('api/v1/', include('apps.opportunities.urls')),
    path('api/v1/', include('apps.recommendations.urls')),
    path('api/v1/', include('apps.ai_agent.urls')),
    path('api/v1/', include('apps.evaluations.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
