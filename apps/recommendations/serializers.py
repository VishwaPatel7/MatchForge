from rest_framework import serializers
from apps.recommendations.models import Recommendation, RecommendationExplanation
from apps.opportunities.serializers import OpportunitySerializer


class RecommendationExplanationSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecommendationExplanation
        fields = [
            'matched_skills', 'missing_skills', 'preference_matches',
            'potential_concerns', 'natural_language_explanation', 'generated_at'
        ]


class RecommendationSerializer(serializers.ModelSerializer):
    opportunity = OpportunitySerializer(read_only=True)
    explanation = RecommendationExplanationSerializer(read_only=True)

    class Meta:
        model = Recommendation
        fields = [
            'id', 'opportunity', 'overall_score', 'semantic_score', 'skill_score',
            'role_score', 'experience_score', 'location_score', 'preference_score',
            'passed_hard_filters', 'exclusion_reasons', 'explanation', 'calculated_at'
        ]
