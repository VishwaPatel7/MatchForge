from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from apps.opportunities.models import Opportunity, SavedOpportunity, SearchHistory
from apps.opportunities.serializers import OpportunitySerializer, SavedOpportunitySerializer
from apps.search.hybrid_search import HybridSearchService
from apps.recommendations.services import OpportunityComparisonService


class OpportunityListView(generics.ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = OpportunitySerializer

    def get_queryset(self):
        qs = Opportunity.objects.filter(is_active=True)
        work_mode = self.request.query_params.get('work_mode')
        emp_type = self.request.query_params.get('employment_type')
        location = self.request.query_params.get('location')
        no_unpaid = self.request.query_params.get('no_unpaid')

        if work_mode:
            qs = qs.filter(work_mode=work_mode)
        if emp_type:
            qs = qs.filter(employment_type=emp_type)
        if location:
            qs = qs.filter(location__icontains=location)
        if no_unpaid and no_unpaid.lower() in ('true', '1'):
            qs = qs.filter(is_unpaid=False)

        return qs


class OpportunityDetailView(generics.RetrieveAPIView):
    permission_classes = [AllowAny]
    serializer_class = OpportunitySerializer
    queryset = Opportunity.objects.filter(is_active=True)
    lookup_field = 'id'


class OpportunitySearchView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        query = request.data.get('query', '')
        filters = request.data.get('filters', {})
        limit = int(request.data.get('limit', 15))

        results = HybridSearchService.search(query=query, filters=filters, limit=limit)

        # Record search history if user is authenticated
        if request.user.is_authenticated:
            SearchHistory.objects.create(
                profile=request.user.profile,
                query=query,
                filters=filters,
                search_type='HYBRID',
                result_count=len(results)
            )

        formatted = [
            {
                "id": str(r['opportunity'].id),
                "title": r['opportunity'].title,
                "company": r['opportunity'].company,
                "location": r['opportunity'].location,
                "work_mode": r['opportunity'].work_mode,
                "employment_type": r['opportunity'].employment_type,
                "stipend": f"{r['opportunity'].currency} {r['opportunity'].min_salary_or_stipend:,.0f} - {r['opportunity'].max_salary_or_stipend:,.0f}" if not r['opportunity'].is_unpaid else "Unpaid",
                "is_unpaid": r['opportunity'].is_unpaid,
                "required_skills": r['opportunity'].required_skills,
                "hybrid_score": r['hybrid_score'],
                "semantic_score": r['semantic_score'],
                "apply_url": r['opportunity'].apply_url,
            }
            for r in results
        ]

        return Response({
            "query": query,
            "count": len(formatted),
            "results": formatted
        })


class OpportunityCompareView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        ids = request.data.get('opportunity_ids', [])
        if not ids or not isinstance(ids, list) or len(ids) < 2:
            return Response({"error": "Please provide a list of at least 2 opportunity IDs."}, status=status.HTTP_400_BAD_REQUEST)

        res = OpportunityComparisonService.compare(ids[:4], request.user.profile)
        return Response(res)


class SavedOpportunityToggleView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, id):
        profile = request.user.profile
        try:
            opp = Opportunity.objects.get(id=id)
        except Opportunity.DoesNotExist:
            return Response({"error": "Opportunity not found."}, status=status.HTTP_404_NOT_FOUND)

        saved = SavedOpportunity.objects.filter(profile=profile, opportunity=opp).first()
        if saved:
            saved.delete()
            return Response({"status": "success", "saved": False, "message": "Removed from saved opportunities."})
        else:
            notes = request.data.get('notes', '')
            SavedOpportunity.objects.create(profile=profile, opportunity=opp, notes=notes)
            return Response({"status": "success", "saved": True, "message": "Opportunity saved successfully."})

    def get(self, request):
        profile = request.user.profile
        saved_qs = SavedOpportunity.objects.filter(profile=profile).select_related('opportunity')
        serializer = SavedOpportunitySerializer(saved_qs, many=True)
        return Response(serializer.data)
