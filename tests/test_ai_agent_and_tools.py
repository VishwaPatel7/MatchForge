import pytest
from django.contrib.auth.models import User
from apps.profiles.models import UserProfile
from apps.ai_agent.tools import GuardedToolDispatcher
from apps.ai_agent.agent import ConversationalAgentOrchestrator
from apps.preferences.models import UserPreference


@pytest.mark.django_db
class TestAIAgentAndGuardedTools:
    def test_guarded_tool_update_preferences_validation(self):
        user = User.objects.create_user(username='agent_user', password='pass')
        profile = UserProfile.objects.create(user=user)

        # Valid arguments
        res = GuardedToolDispatcher.execute_tool(
            tool_name='update_user_preferences',
            arguments={
                'preferred_roles': ['Backend Developer Intern'],
                'preferred_skills': ['Python', 'Django'],
                'work_mode': ['Remote'],
                'no_unpaid': True
            },
            profile=profile
        )
        assert res['status'] == 'success'
        assert UserPreference.objects.filter(profile=profile, preference_key='no_unpaid').exists()
        pref = UserPreference.objects.get(profile=profile, preference_key='no_unpaid')
        assert pref.is_hard_dealbreaker is True

    def test_guarded_tool_invalid_argument_handling(self):
        user = User.objects.create_user(username='invalid_user', password='pass')
        profile = UserProfile.objects.create(user=user)

        # Passing an invalid type (e.g. dictionary for a list)
        res = GuardedToolDispatcher.execute_tool(
            tool_name='update_user_preferences',
            arguments={'preferred_roles': 12345},  # Int instead of list
            profile=profile
        )
        assert 'error' in res
        assert 'Validation failed' in res['error']

    def test_conversational_agent_message_processing(self):
        user = User.objects.create_user(username='convo_user', password='pass')
        profile = UserProfile.objects.create(user=user, headline='Junior Engineer')

        message_text = "I want a remote backend internship using Python and Django. I don't want unpaid internships."
        res = ConversationalAgentOrchestrator.process_message(
            profile=profile,
            user_message=message_text
        )

        assert 'conversation_id' in res
        assert res['tool_calls_executed'] >= 1
        assert len(res['message']) > 10

        # Check that preferences were saved
        prefs = res['active_preferences']
        assert prefs.get('no_unpaid') is True
        assert 'Remote' in prefs.get('work_mode', [])
