from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from apps.preferences.models import UserPreference, PreferenceHistory
from apps.preferences.serializers import UserPreferenceSerializer, PreferenceHistorySerializer
from apps.preferences.services import PreferenceManager


class PreferenceListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile = request.user.profile
        prefs = UserPreference.objects.filter(profile=profile, is_active=True)
        serializer = UserPreferenceSerializer(prefs, many=True)
        return Response({
            "active_preferences": PreferenceManager.get_user_preferences(profile),
            "dealbreakers": PreferenceManager.get_dealbreakers(profile),
            "records": serializer.data
        })

    def put(self, request):
        profile = request.user.profile
        data = request.data
        if not isinstance(data, dict):
            return Response({"error": "Payload must be a JSON dictionary of key-value preferences."}, status=status.HTTP_400_BAD_REQUEST)

        updated = PreferenceManager.batch_update_preferences(profile, data, source_conversation_id="api_direct_update")
        return Response({
            "status": "success",
            "message": f"Updated {len(updated)} preferences.",
            "results": updated,
            "active_preferences": PreferenceManager.get_user_preferences(profile)
        })


class PreferenceHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile = request.user.profile
        history = PreferenceHistory.objects.filter(preference__profile=profile).select_related('preference')
        serializer = PreferenceHistorySerializer(history, many=True)
        return Response(serializer.data)
