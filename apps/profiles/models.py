import uuid
from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    """
    Extends Django's User model with candidate specific fields, experience,
    location, relocation willingness, and structured profile metadata.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    headline = models.CharField(max_length=255, blank=True, default='')
    bio = models.TextField(blank=True, default='')
    current_location = models.CharField(max_length=150, blank=True, default='')
    willing_to_relocate = models.BooleanField(default=True)
    preferred_work_modes = models.JSONField(default=list, blank=True, help_text="List of preferred work modes: Remote, Hybrid, Onsite")
    experience_months = models.PositiveIntegerField(default=0, help_text="Total professional or internship experience in months")
    target_roles = models.JSONField(default=list, blank=True, help_text="Target role titles e.g. ['Backend Developer', 'Software Engineer Intern']")
    parsed_metadata = models.JSONField(default=dict, blank=True, help_text="Consolidated parsed profile data from resumes")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'matchforge_user_profiles'
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['current_location']),
        ]

    def __str__(self):
        return f"{self.user.username} ({self.headline or 'Candidate'})"

    @property
    def full_name(self):
        name = f"{self.user.first_name} {self.user.last_name}".strip()
        return name or self.user.username
