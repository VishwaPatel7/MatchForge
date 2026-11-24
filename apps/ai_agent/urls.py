from django.urls import path
from apps.ai_agent.views import ConversationListCreateView, ChatMessageView

urlpatterns = [
    path('agent/conversations/', ConversationListCreateView.as_view(), name='api-agent-conversations'),
    path('agent/conversations/<uuid:id>/messages/', ChatMessageView.as_view(), name='api-agent-messages'),
]
