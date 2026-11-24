from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from apps.evaluations.models import EvaluationRun
from apps.evaluations.services import EvaluationFrameworkService


class RunEvaluationView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        eval_run = EvaluationFrameworkService.run_benchmark()
        return Response({
            "status": "success",
            "message": f"Benchmark completed across {eval_run.sample_size} test items.",
            "metrics": {
                "precision_at_k": eval_run.precision_at_k,
                "recall_at_k": eval_run.recall_at_k,
                "mrr": eval_run.mrr,
                "ndcg_at_k": eval_run.ndcg_at_k,
                "dealbreaker_violation_rate": f"{eval_run.dealbreaker_violation_rate}%",
                "tool_selection_accuracy": f"{eval_run.tool_selection_accuracy}%",
                "structured_output_validity": f"{eval_run.structured_output_validity}%",
                "avg_search_latency_ms": f"{eval_run.avg_search_latency_ms} ms",
            },
            "comparison": eval_run.comparison_report,
            "executed_at": eval_run.executed_at,
        })


class LatestEvaluationView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        latest = EvaluationRun.objects.first()
        if not latest:
            # Run initial benchmark if none exists
            latest = EvaluationFrameworkService.run_benchmark()

        return Response({
            "id": str(latest.id),
            "sample_size": latest.sample_size,
            "metrics": {
                "precision_at_k": latest.precision_at_k,
                "recall_at_k": latest.recall_at_k,
                "mrr": latest.mrr,
                "ndcg_at_k": latest.ndcg_at_k,
                "dealbreaker_violation_rate": latest.dealbreaker_violation_rate,
                "skill_match_accuracy": latest.skill_match_accuracy,
                "preference_satisfaction_rate": latest.preference_satisfaction_rate,
                "tool_selection_accuracy": latest.tool_selection_accuracy,
                "structured_output_validity": latest.structured_output_validity,
                "avg_search_latency_ms": latest.avg_search_latency_ms,
            },
            "comparison": latest.comparison_report,
            "executed_at": latest.executed_at,
        })
