from django.urls import path
from apps.recommendations.views import (
    GenerateRecommendationsView,
    RecommendationListView,
    RecommendationExplanationView,
    SkillGapAnalyticsView
)

urlpatterns = [
    path('recommendations/generate/', GenerateRecommendationsView.as_view(), name='api-recommendations-generate'),
    path('recommendations/', RecommendationListView.as_view(), name='api-recommendations-list'),
    path('recommendations/<uuid:id>/explanation/', RecommendationExplanationView.as_view(), name='api-recommendation-explanation'),
    path('analytics/skill-gaps/', SkillGapAnalyticsView.as_view(), name='api-analytics-skill-gaps'),
]
