import uuid
from django.db import models
from apps.profiles.models import UserProfile


class UserPreference(models.Model):
    """
    Candidate preference with support for versioning, priority levels,
    and zero-tolerance dealbreaker flags.
    """
    PREFERENCE_TYPES = [
        ('STRING', 'Single String'),
        ('LIST', 'List of Strings'),
        ('BOOLEAN', 'Boolean Flag'),
        ('NUMBER', 'Numeric Value'),
        ('RANGE', 'Numeric Range'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='preferences')
    preference_key = models.CharField(max_length=100, help_text="e.g. work_mode, no_unpaid, target_roles, excluded_locations")
    preference_value = models.JSONField(help_text="Arbitrary structured JSON value")
    preference_type = models.CharField(max_length=20, choices=PREFERENCE_TYPES, default='LIST')
    priority_level = models.PositiveSmallIntegerField(default=3, help_text="1 (Nice to have) to 5 (Crucial)")
    is_hard_dealbreaker = models.BooleanField(default=False, help_text="If True, violation causes immediate zero-tolerance exclusion")
    version = models.PositiveIntegerField(default=1)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'matchforge_user_preferences'
        unique_together = ('profile', 'preference_key')
        verbose_name = 'User Preference'
        verbose_name_plural = 'User Preferences'
        indexes = [
            models.Index(fields=['profile', 'is_hard_dealbreaker']),
            models.Index(fields=['profile', 'preference_key']),
        ]

    def __str__(self):
        dealbreaker_badge = " [DEALBREAKER]" if self.is_hard_dealbreaker else ""
        return f"{self.profile.user.username} - {self.preference_key}: {self.preference_value}{dealbreaker_badge} (v{self.version})"


class PreferenceHistory(models.Model):
    """
    Audit log tracking each mutation, conflict resolution, and update origin
    across multi-turn conversations.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    preference = models.ForeignKey(UserPreference, on_delete=models.CASCADE, related_name='history')
    old_value = models.JSONField(null=True, blank=True)
    new_value = models.JSONField()
    version = models.PositiveIntegerField(default=1)
    update_reason = models.CharField(max_length=255, default='Updated via conversational AI agent')
    source_conversation_id = models.CharField(max_length=100, blank=True, default='')
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'matchforge_preference_history'
        verbose_name = 'Preference History'
        verbose_name_plural = 'Preference History Entries'
        ordering = ['-changed_at']
        indexes = [
            models.Index(fields=['preference', '-changed_at']),
        ]

    def __str__(self):
        return f"History v{self.version} for {self.preference.preference_key} @ {self.changed_at.strftime('%Y-%m-%d %H:%M')}"
