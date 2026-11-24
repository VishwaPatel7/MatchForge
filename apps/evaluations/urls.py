from django.urls import path
from apps.evaluations.views import RunEvaluationView, LatestEvaluationView

urlpatterns = [
    path('evaluations/run/', RunEvaluationView.as_view(), name='api-evaluations-run'),
    path('evaluations/latest/', LatestEvaluationView.as_view(), name='api-evaluations-latest'),
]
