import uuid
from django.db import models
from apps.profiles.models import UserProfile


class Conversation(models.Model):
    """
    Multi-turn conversation session between candidate and the MatchForge AI Agent.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='conversations')
    title = models.CharField(max_length=200, default='New Opportunity Discovery Session')
    is_active = models.BooleanField(default=True)
    started_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'matchforge_conversations'
        verbose_name = 'Conversation'
        verbose_name_plural = 'Conversations'
        ordering = ['-last_activity']
        indexes = [
            models.Index(fields=['profile', '-last_activity']),
        ]

    def __str__(self):
        return f"{self.profile.user.username} - {self.title}"


class ChatMessage(models.Model):
    """
    Individual turn within a conversation session, supporting function/tool calls and results.
    """
    SENDER_TYPES = [
        ('USER', 'Candidate User'),
        ('ASSISTANT', 'AI Assistant'),
        ('SYSTEM', 'System Prompt / Directive'),
        ('TOOL', 'Tool Execution Result'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender_type = models.CharField(max_length=20, choices=SENDER_TYPES)
    content = models.TextField(blank=True, default='')
    
    # Tool calling support
    tool_calls = models.JSONField(null=True, blank=True, help_text="List of tool invocations emitted by the LLM")
    tool_responses = models.JSONField(null=True, blank=True, help_text="Results of backend tool executions")
    metadata = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'matchforge_chat_messages'
        verbose_name = 'Chat Message'
        verbose_name_plural = 'Chat Messages'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['conversation', 'created_at']),
            models.Index(fields=['sender_type']),
        ]

    def __str__(self):
        return f"[{self.sender_type}] {self.content[:40]}..."
