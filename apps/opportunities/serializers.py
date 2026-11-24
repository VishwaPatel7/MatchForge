from rest_framework import serializers
from apps.opportunities.models import Opportunity, SavedOpportunity, SearchHistory


class OpportunitySerializer(serializers.ModelSerializer):
    stipend_display = serializers.SerializerMethodField()

    class Meta:
        model = Opportunity
        fields = [
            'id', 'title', 'company', 'description', 'location', 'work_mode',
            'employment_type', 'min_experience_months', 'max_experience_months',
            'min_salary_or_stipend', 'max_salary_or_stipend', 'currency',
            'is_unpaid', 'stipend_display', 'required_skills', 'preferred_skills',
            'apply_url', 'posted_date'
        ]

    def get_stipend_display(self, obj):
        if obj.is_unpaid:
            return "Unpaid"
        return f"{obj.currency} {obj.min_salary_or_stipend:,.0f} - {obj.max_salary_or_stipend:,.0f}"


class SavedOpportunitySerializer(serializers.ModelSerializer):
    opportunity = OpportunitySerializer(read_only=True)

    class Meta:
        model = SavedOpportunity
        fields = ['id', 'opportunity', 'notes', 'saved_at']
