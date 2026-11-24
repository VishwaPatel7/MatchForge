import uuid
from django.db import models
from apps.profiles.models import UserProfile


class Opportunity(models.Model):
    """
    Central job / internship opportunity record.
    Supports structured attributes for hard filtering and rich text for semantic retrieval.
    """
    WORK_MODE_CHOICES = [
        ('Remote', 'Remote'),
        ('Hybrid', 'Hybrid'),
        ('Onsite', 'Onsite'),
    ]

    EMPLOYMENT_TYPE_CHOICES = [
        ('Internship', 'Internship'),
        ('Full-time', 'Full-time'),
        ('Part-time', 'Part-time'),
        ('Contract', 'Contract'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255, db_index=True)
    company = models.CharField(max_length=200, db_index=True)
    description = models.TextField()
    location = models.CharField(max_length=150, db_index=True)
    work_mode = models.CharField(max_length=20, choices=WORK_MODE_CHOICES, default='Remote', db_index=True)
    employment_type = models.CharField(max_length=30, choices=EMPLOYMENT_TYPE_CHOICES, default='Internship', db_index=True)
    
    min_experience_months = models.PositiveIntegerField(default=0)
    max_experience_months = models.PositiveIntegerField(default=12)
    
    min_salary_or_stipend = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    max_salary_or_stipend = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    currency = models.CharField(max_length=10, default='INR')
    is_unpaid = models.BooleanField(default=False, db_index=True)
    
    required_skills = models.JSONField(default=list, help_text="List of mandatory technical skills")
    preferred_skills = models.JSONField(default=list, help_text="List of good-to-have skills")
    
    apply_url = models.URLField(max_length=500, blank=True, default='')
    source = models.CharField(max_length=100, default='MatchForge Ingestion')
    is_active = models.BooleanField(default=True, db_index=True)
    
    posted_date = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'matchforge_opportunities'
        verbose_name = 'Opportunity'
        verbose_name_plural = 'Opportunities'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['is_active', 'employment_type', 'work_mode']),
            models.Index(fields=['company', 'is_active']),
            models.Index(fields=['location', 'work_mode']),
            models.Index(fields=['is_unpaid']),
        ]

    def __str__(self):
        return f"{self.title} @ {self.company} ({self.work_mode})"


class OpportunityEmbedding(models.Model):
    """
    Vector representation of an opportunity for semantic search and cosine similarity.
    Stored as JSON array of floats for universal SQLite + PostgreSQL portability.
    """
    opportunity = models.OneToOneField(Opportunity, on_delete=models.CASCADE, primary_key=True, related_name='embedding_record')
    embedding = models.JSONField(help_text="Vector floats representing the opportunity document")
    dimensions = models.PositiveIntegerField(default=384)
    model_name = models.CharField(max_length=100, default='all-MiniLM-L6-v2-fallback')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'matchforge_opportunity_embeddings'
        verbose_name = 'Opportunity Embedding'
        verbose_name_plural = 'Opportunity Embeddings'

    def __str__(self):
        return f"Embedding for {self.opportunity.title} ({self.dimensions}d)"


class SavedOpportunity(models.Model):
    """
    Opportunities bookmarked by a candidate for later review or application tracking.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='saved_opportunities')
    opportunity = models.ForeignKey(Opportunity, on_delete=models.CASCADE, related_name='saved_by_users')
    notes = models.TextField(blank=True, default='')
    saved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'matchforge_saved_opportunities'
        unique_together = ('profile', 'opportunity')
        verbose_name = 'Saved Opportunity'
        verbose_name_plural = 'Saved Opportunities'
        indexes = [
            models.Index(fields=['profile', '-saved_at']),
        ]

    def __str__(self):
        return f"{self.profile.user.username} saved {self.opportunity.title}"


class SearchHistory(models.Model):
    """
    Audit log of candidate searches, supporting search analytics and recommendation refinement.
    """
    SEARCH_TYPES = [
        ('KEYWORD', 'Keyword Search'),
        ('SEMANTIC', 'Semantic Vector Search'),
        ('HYBRID', 'Hybrid Search'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='searches')
    query = models.CharField(max_length=500)
    filters = models.JSONField(default=dict, blank=True)
    search_type = models.CharField(max_length=20, choices=SEARCH_TYPES, default='HYBRID')
    result_count = models.PositiveIntegerField(default=0)
    executed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'matchforge_search_history'
        verbose_name = 'Search History'
        verbose_name_plural = 'Search History'
        ordering = ['-executed_at']
        indexes = [
            models.Index(fields=['profile', '-executed_at']),
        ]

    def __str__(self):
        return f"{self.profile.user.username} - '{self.query}' ({self.search_type})"
