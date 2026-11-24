from typing import Dict, Any, List, Optional, Tuple
from django.db import transaction
from apps.profiles.models import UserProfile
from apps.preferences.models import UserPreference, PreferenceHistory


class PreferenceManager:
    """
    State machine for persistent conversational preferences with versioning,
    conflict resolution, and zero-tolerance dealbreaker classification.
    """

    KNOWN_DEALBREAKER_KEYS = {
        'no_unpaid': True,
        'exclude_unpaid': True,
        'prohibited_companies': True,
        'excluded_locations': True,
        'required_work_mode': True,
    }

    @classmethod
    def get_user_preferences(cls, profile: UserProfile) -> Dict[str, Any]:
        """Returns a consolidated dictionary of all active user preferences."""
        prefs = UserPreference.objects.filter(profile=profile, is_active=True)
        return {p.preference_key: p.preference_value for p in prefs}

    @classmethod
    def get_dealbreakers(cls, profile: UserProfile) -> Dict[str, Any]:
        """Returns only hard dealbreakers."""
        dealbreakers = UserPreference.objects.filter(profile=profile, is_active=True, is_hard_dealbreaker=True)
        return {p.preference_key: p.preference_value for p in dealbreakers}

    @classmethod
    @transaction.atomic
    def set_preference(
        cls,
        profile: UserProfile,
        key: str,
        value: Any,
        is_dealbreaker: Optional[bool] = None,
        priority: int = 3,
        reason: str = "Updated via AI conversation",
        source_conversation_id: str = ""
    ) -> Tuple[UserPreference, bool, bool]:
        """
        Updates an existing preference or creates a new one.
        Handles conflict resolution, version increments, and audit history.
        Returns (preference, created, conflict_resolved).
        """
        normalized_key = key.strip().lower()
        
        # Auto-detect dealbreaker status if not explicitly passed
        if is_dealbreaker is None:
            is_dealbreaker = cls.KNOWN_DEALBREAKER_KEYS.get(normalized_key, False)

        pref = UserPreference.objects.filter(profile=profile, preference_key=normalized_key).first()
        
        if pref:
            old_value = pref.preference_value
            conflict_detected = (old_value != value)
            
            if conflict_detected:
                pref.version += 1
                pref.preference_value = value
                if is_dealbreaker:
                    pref.is_hard_dealbreaker = True
                pref.priority_level = priority
                pref.save()
                
                # Record audit history
                PreferenceHistory.objects.create(
                    preference=pref,
                    old_value=old_value,
                    new_value=value,
                    version=pref.version,
                    update_reason=reason,
                    source_conversation_id=source_conversation_id,
                )
            return pref, False, conflict_detected
        else:
            # Create new preference
            pref = UserPreference.objects.create(
                profile=profile,
                preference_key=normalized_key,
                preference_value=value,
                priority_level=priority,
                is_hard_dealbreaker=is_dealbreaker,
                version=1,
            )
            PreferenceHistory.objects.create(
                preference=pref,
                old_value=None,
                new_value=value,
                version=1,
                update_reason=reason,
                source_conversation_id=source_conversation_id,
            )
            return pref, True, False

    @classmethod
    def batch_update_preferences(
        cls,
        profile: UserProfile,
        preferences_dict: Dict[str, Any],
        source_conversation_id: str = ""
    ) -> List[Dict[str, Any]]:
        """
        Processes a batch of extracted structured preferences from the AI agent.
        """
        results = []
        for key, val in preferences_dict.items():
            if val is None or val == "" or val == []:
                continue
                
            # If the user says unpaid is not allowed
            is_dealbreaker = None
            if key in ('no_unpaid', 'exclude_unpaid', 'unpaid_prohibited'):
                is_dealbreaker = True
                key = 'no_unpaid'
                val = bool(val)
                
            pref, created, conflict = cls.set_preference(
                profile=profile,
                key=key,
                value=val,
                is_dealbreaker=is_dealbreaker,
                source_conversation_id=source_conversation_id,
            )
            results.append({
                'key': key,
                'value': val,
                'created': created,
                'conflict_resolved': conflict,
                'version': pref.version,
                'is_dealbreaker': pref.is_hard_dealbreaker,
            })
        return results
