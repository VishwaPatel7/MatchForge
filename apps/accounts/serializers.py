from django.contrib.auth.models import User
from rest_framework import serializers
from apps.profiles.models import UserProfile


class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)
    full_name = serializers.CharField(write_only=True, required=False, default='')
    current_location = serializers.CharField(write_only=True, required=False, default='')

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'full_name', 'current_location']

    def create(self, validated_data):
        full_name = validated_data.pop('full_name', '')
        location = validated_data.pop('current_location', '')
        password = validated_data.pop('password')
        
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=password
        )
        if full_name:
            parts = full_name.split(' ', 1)
            user.first_name = parts[0]
            if len(parts) > 1:
                user.last_name = parts[1]
            user.save()

        # Create corresponding profile
        UserProfile.objects.create(
            user=user,
            current_location=location
        )
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.CharField(source='user.email', read_only=True)
    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = UserProfile
        fields = [
            'id', 'username', 'email', 'full_name', 'headline', 'bio',
            'current_location', 'willing_to_relocate', 'preferred_work_modes',
            'experience_months', 'target_roles', 'parsed_metadata', 'created_at'
        ]
        read_only_fields = ['id', 'parsed_metadata', 'created_at']
