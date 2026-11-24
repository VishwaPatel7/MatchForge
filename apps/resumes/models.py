import uuid
from django.db import models
from apps.profiles.models import UserProfile


class CandidateResume(models.Model):
    """
    Stores uploaded PDF resumes, raw extracted text, parsing state,
    and structured extraction results.
    """
    STATUS_PENDING = 'PENDING'
    STATUS_PROCESSING = 'PROCESSING'
    STATUS_COMPLETED = 'COMPLETED'
    STATUS_FAILED = 'FAILED'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_PROCESSING, 'Processing'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_FAILED, 'Failed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='resumes')
    file = models.FileField(upload_to='resumes/%Y/%m/')
    file_name = models.CharField(max_length=255)
    file_size = models.PositiveIntegerField(help_text="File size in bytes")
    file_hash = models.CharField(max_length=64, blank=True, help_text="SHA256 hash for deduplication")
    raw_text = models.TextField(blank=True, default='')
    parsing_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    error_message = models.TextField(blank=True, default='')
    completeness_score = models.FloatField(default=0.0, help_text="Resume completeness metric 0-100")
    
    # Structured extractions
    education = models.JSONField(default=list, blank=True)
    experience = models.JSONField(default=list, blank=True)
    projects = models.JSONField(default=list, blank=True)
    certifications = models.JSONField(default=list, blank=True)
    
    is_active = models.BooleanField(default=True, help_text="Whether this is the primary active resume for recommendations")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'matchforge_candidate_resumes'
        verbose_name = 'Candidate Resume'
        verbose_name_plural = 'Candidate Resumes'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['profile', 'is_active']),
            models.Index(fields=['file_hash']),
            models.Index(fields=['parsing_status']),
        ]

    def __str__(self):
        return f"{self.profile.user.username} - {self.file_name} ({self.parsing_status})"


class ExtractedSkill(models.Model):
    """
    Fine-grained skill extracted from a candidate's resume or explicitly verified.
    """
    CATEGORY_CHOICES = [
        ('LANGUAGE', 'Programming Language'),
        ('FRAMEWORK', 'Framework / Library'),
        ('DATABASE', 'Database / Storage'),
        ('DEVOPS', 'DevOps / Cloud / Tooling'),
        ('ARCHITECTURE', 'System Architecture & Concepts'),
        ('GENERAL', 'General Technical Skill'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    resume = models.ForeignKey(CandidateResume, on_delete=models.CASCADE, related_name='extracted_skills')
    name = models.CharField(max_length=100)
    normalized_name = models.CharField(max_length=100, db_index=True)
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default='GENERAL')
    proficiency_level = models.PositiveSmallIntegerField(default=3, help_text="1 (Beginner) to 5 (Expert)")
    confidence_score = models.FloatField(default=1.0, help_text="Extraction confidence score 0.0 - 1.0")
    years_of_experience = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'matchforge_extracted_skills'
        verbose_name = 'Extracted Skill'
        verbose_name_plural = 'Extracted Skills'
        indexes = [
            models.Index(fields=['normalized_name']),
            models.Index(fields=['category']),
            models.Index(fields=['resume', 'normalized_name']),
        ]

    def __str__(self):
        return f"{self.name} ({self.category})"
