import uuid
from django.db import models


class EvaluationRun(models.Model):
    """
    Stores metrics and timing from executing the offline/online evaluation benchmark suite.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, default='Standard MatchForge Benchmark Suite')
    sample_size = models.PositiveIntegerField(default=50)
    
    # Retrieval Metrics
    precision_at_k = models.FloatField(default=0.0)
    recall_at_k = models.FloatField(default=0.0)
    mrr = models.FloatField(default=0.0, help_text="Mean Reciprocal Rank")
    ndcg_at_k = models.FloatField(default=0.0, help_text="Normalized Discounted Cumulative Gain")
    
    # Recommendation Quality
    dealbreaker_violation_rate = models.FloatField(default=0.0, help_text="Must be 0.00% in a reliable system")
    skill_match_accuracy = models.FloatField(default=0.0)
    preference_satisfaction_rate = models.FloatField(default=0.0)
    
    # LLM & Agent Metrics
    structured_output_validity = models.FloatField(default=0.0)
    tool_selection_accuracy = models.FloatField(default=0.0)
    explanation_faithfulness = models.FloatField(default=0.0)
    
    # Latency & System Metrics (in milliseconds)
    avg_search_latency_ms = models.FloatField(default=0.0)
    avg_recommendation_latency_ms = models.FloatField(default=0.0)
    error_rate = models.FloatField(default=0.0)
    
    comparison_report = models.JSONField(default=dict, blank=True, help_text="Comparison between Keyword, Semantic, and Hybrid retrieval")
    raw_logs = models.TextField(blank=True, default='')
    executed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'matchforge_evaluation_runs'
        verbose_name = 'Evaluation Run'
        verbose_name_plural = 'Evaluation Runs'
        ordering = ['-executed_at']

    def __str__(self):
        return f"Eval Run {self.id} @ {self.executed_at.strftime('%Y-%m-%d %H:%M')} (NDCG: {self.ndcg_at_k:.2f})"
