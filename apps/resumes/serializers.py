from rest_framework import serializers
from apps.resumes.models import CandidateResume, ExtractedSkill


class ExtractedSkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExtractedSkill
        fields = ['id', 'name', 'normalized_name', 'category', 'proficiency_level', 'confidence_score']


class CandidateResumeSerializer(serializers.ModelSerializer):
    extracted_skills = ExtractedSkillSerializer(many=True, read_only=True)

    class Meta:
        model = CandidateResume
        fields = [
            'id', 'file_name', 'file_size', 'file_hash', 'parsing_status',
            'completeness_score', 'education', 'experience', 'projects',
            'certifications', 'extracted_skills', 'is_active', 'created_at'
        ]
