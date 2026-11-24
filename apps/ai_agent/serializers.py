from rest_framework import serializers
from apps.ai_agent.models import Conversation, ChatMessage


class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = ['id', 'sender_type', 'content', 'tool_calls', 'tool_responses', 'metadata', 'created_at']


class ConversationSerializer(serializers.ModelSerializer):
    messages = ChatMessageSerializer(many=True, read_only=True)

    class Meta:
        model = Conversation
        fields = ['id', 'title', 'is_active', 'started_at', 'last_activity', 'messages']
