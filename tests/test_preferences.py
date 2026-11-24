import pytest
from django.contrib.auth.models import User
from apps.profiles.models import UserProfile
from apps.preferences.models import UserPreference, PreferenceHistory
from apps.preferences.services import PreferenceManager


@pytest.mark.django_db
class TestPreferenceMemoryAndConflicts:
    def test_preference_creation_and_versioning(self):
        user = User.objects.create_user(username='pref_user', password='pass')
        profile = UserProfile.objects.create(user=user)

        # First turn: User states remote preference
        pref, created, conflict = PreferenceManager.set_preference(
            profile=profile,
            key='work_mode',
            value=['Remote'],
            source_conversation_id='conv_1'
        )
        assert created is True
        assert conflict is False
        assert pref.version == 1
        assert pref.preference_value == ['Remote']

        # Second turn: User updates preference to Hybrid & Bangalore
        pref_updated, created_2, conflict_2 = PreferenceManager.set_preference(
            profile=profile,
            key='work_mode',
            value=['Hybrid', 'Remote'],
            source_conversation_id='conv_2'
        )
        assert created_2 is False
        assert conflict_2 is True
        assert pref_updated.version == 2
        assert pref_updated.preference_value == ['Hybrid', 'Remote']

        # Verify audit history log
        history_records = PreferenceHistory.objects.filter(preference=pref_updated).order_by('-version')
        assert history_records.count() == 2
        latest_hist = history_records.first()
        assert latest_hist.old_value == ['Remote']
        assert latest_hist.new_value == ['Hybrid', 'Remote']

    def test_dealbreaker_automatic_detection(self):
        user = User.objects.create_user(username='dealbreaker_user', password='pass')
        profile = UserProfile.objects.create(user=user)

        pref, _, _ = PreferenceManager.set_preference(
            profile=profile,
            key='no_unpaid',
            value=True
        )
        assert pref.is_hard_dealbreaker is True
        dealbreakers = PreferenceManager.get_dealbreakers(profile)
        assert 'no_unpaid' in dealbreakers
