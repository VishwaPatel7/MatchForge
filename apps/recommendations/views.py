from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from apps.recommendations.models import Recommendation, RecommendationExplanation
from apps.recommendations.serializers import RecommendationSerializer, RecommendationExplanationSerializer
from apps.recommendations.services import HybridRecommendationEngine, SkillGapAnalyzer


class GenerateRecommendationsView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        profile = request.user.profile
        recs = HybridRecommendationEngine.generate_recommendations_for_user(profile, limit=25, recompute=True)
        serializer = RecommendationSerializer(recs, many=True)
        return Response({
            "status": "success",
            "count": len(recs),
            "recommendations": serializer.data
        })


class RecommendationListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile = request.user.profile
        recs = Recommendation.objects.filter(profile=profile).select_related('opportunity', 'explanation')
        
        # If no recommendations computed yet, trigger computation
        if not recs.exists():
            recs = HybridRecommendationEngine.generate_recommendations_for_user(profile, limit=20)

        # Allow filtering to only passed_hard_filters
        passed_only = request.query_params.get('passed_only', 'true').lower() in ('true', '1')
        if passed_only:
            recs = [r for r in recs if r.passed_hard_filters]

        serializer = RecommendationSerializer(recs, many=True)
        return Response(serializer.data)


class RecommendationExplanationView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id):
        profile = request.user.profile
        try:
            rec = Recommendation.objects.select_related('opportunity', 'explanation').get(id=id, profile=profile)
        except Recommendation.DoesNotExist:
            return Response({"error": "Recommendation not found."}, status=status.HTTP_404_NOT_FOUND)

        if not hasattr(rec, 'explanation'):
            return Response({"error": "No explanation generated for this recommendation."}, status=status.HTTP_404_NOT_FOUND)

        serializer = RecommendationExplanationSerializer(rec.explanation)
        return Response({
            "recommendation_id": str(rec.id),
            "opportunity_title": rec.opportunity.title,
            "company": rec.opportunity.company,
            "overall_score": float(rec.overall_score),
            "passed_hard_filters": rec.passed_hard_filters,
            "exclusion_reasons": rec.exclusion_reasons,
            "score_breakdown": {
                "semantic": float(rec.semantic_score),
                "skills": float(rec.skill_score),
                "role": float(rec.role_score),
                "experience": float(rec.experience_score),
                "location": float(rec.location_score),
                "preferences": float(rec.preference_score),
            },
            "explanation": serializer.data
        })


class SkillGapAnalyticsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile = request.user.profile
        res = SkillGapAnalyzer.analyze_candidate_gaps(profile)
        return Response(res)
