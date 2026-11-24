from rest_framework import serializers
from apps.preferences.models import UserPreference, PreferenceHistory


class UserPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserPreference
        fields = [
            'id', 'preference_key', 'preference_value', 'preference_type',
            'priority_level', 'is_hard_dealbreaker', 'version', 'updated_at'
        ]


class PreferenceHistorySerializer(serializers.ModelSerializer):
    preference_key = serializers.CharField(source='preference.preference_key', read_only=True)

    class Meta:
        model = PreferenceHistory
        fields = [
            'id', 'preference_key', 'old_value', 'new_value',
            'version', 'update_reason', 'source_conversation_id', 'changed_at'
        ]
