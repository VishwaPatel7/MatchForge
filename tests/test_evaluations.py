import pytest
from apps.evaluations.services import EvaluationFrameworkService
from apps.opportunities.models import Opportunity


@pytest.mark.django_db
class TestEvaluationFramework:
    def test_run_benchmark_suite(self):
        # Ensure at least sample opportunities exist
        if Opportunity.objects.count() < 10:
            from django.core.management import call_command
            call_command('ingest_opportunities', count=30)

        eval_run = EvaluationFrameworkService.run_benchmark()

        assert eval_run.sample_size == 50
        assert eval_run.ndcg_at_k > 0.0
        assert eval_run.mrr > 0.0
        assert eval_run.precision_at_k > 0.0
        # Crucial invariant: zero tolerance for dealbreaker violations
        assert eval_run.dealbreaker_violation_rate == 0.0
        assert 'retrieval_comparison' in eval_run.comparison_report
