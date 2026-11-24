from typing import Dict, Any, List
from pydantic import ValidationError
from apps.profiles.models import UserProfile
from apps.preferences.services import PreferenceManager
from apps.search.hybrid_search import HybridSearchService
from apps.recommendations.services import (
    HybridRecommendationEngine,
    SkillGapAnalyzer,
    OpportunityComparisonService
)
from apps.opportunities.models import Opportunity
from apps.ai_agent.schemas import (
    UpdatePreferencesSchema,
    SearchOpportunitiesSchema,
    CompareOpportunitiesSchema,
    ExplainRecommendationSchema,
    IdentifySkillGapsSchema,
    GetUserProfileSchema,
)


class GuardedToolDispatcher:
    """
    Guarded tool execution framework.
    Strictly validates arguments against Pydantic schemas, enforces candidate authorization,
    and dispatches calls to verified backend domain services without allowing arbitrary database operations.
    """

    TOOL_DEFINITIONS = [
        {
            "type": "function",
            "function": {
                "name": "update_user_preferences",
                "description": "Updates or overrides candidate preferences, location desires, and hard dealbreakers.",
                "parameters": UpdatePreferencesSchema.model_json_schema()
            }
        },
        {
            "type": "function",
            "function": {
                "name": "search_opportunities",
                "description": "Searches opportunities using hybrid semantic and keyword retrieval.",
                "parameters": SearchOpportunitiesSchema.model_json_schema()
            }
        },
        {
            "type": "function",
            "function": {
                "name": "compare_opportunities",
                "description": "Generates a structured side-by-side trade-off comparison between 2 to 4 opportunities.",
                "parameters": CompareOpportunitiesSchema.model_json_schema()
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_user_profile",
                "description": "Retrieves the current candidate's profile, parsed resume skills, and active preferences.",
                "parameters": GetUserProfileSchema.model_json_schema()
            }
        },
        {
            "type": "function",
            "function": {
                "name": "explain_recommendation",
                "description": "Fetches a grounded score breakdown, skill matches, and potential concerns for a recommended opportunity.",
                "parameters": ExplainRecommendationSchema.model_json_schema()
            }
        },
        {
            "type": "function",
            "function": {
                "name": "identify_skill_gaps",
                "description": "Analyzes the most frequent missing skills required by top opportunities matching the candidate.",
                "parameters": IdentifySkillGapsSchema.model_json_schema()
            }
        }
    ]

    @classmethod
    def execute_tool(cls, tool_name: str, arguments: Dict[str, Any], profile: UserProfile, conversation_id: str = "") -> Dict[str, Any]:
        """
        Validates arguments and dispatches to the matching safe handler.
        """
        try:
            if tool_name == "update_user_preferences":
                validated = UpdatePreferencesSchema(**arguments)
                return cls._tool_update_user_preferences(validated, profile, conversation_id)
                
            elif tool_name == "search_opportunities":
                validated = SearchOpportunitiesSchema(**arguments)
                return cls._tool_search_opportunities(validated, profile)
                
            elif tool_name == "compare_opportunities":
                validated = CompareOpportunitiesSchema(**arguments)
                return cls._tool_compare_opportunities(validated, profile)
                
            elif tool_name == "get_user_profile":
                validated = GetUserProfileSchema(**arguments)
                return cls._tool_get_user_profile(validated, profile)
                
            elif tool_name == "explain_recommendation":
                validated = ExplainRecommendationSchema(**arguments)
                return cls._tool_explain_recommendation(validated, profile)
                
            elif tool_name == "identify_skill_gaps":
                validated = IdentifySkillGapsSchema(**arguments)
                return cls._tool_identify_skill_gaps(validated, profile)
                
            else:
                return {"error": f"Unknown tool: '{tool_name}'"}
                
        except ValidationError as val_err:
            return {"error": f"Validation failed for tool '{tool_name}': {val_err.errors()}"}
        except Exception as e:
            return {"error": f"Error executing tool '{tool_name}': {str(e)}"}

    @classmethod
    def _tool_update_user_preferences(cls, params: UpdatePreferencesSchema, profile: UserProfile, conversation_id: str) -> Dict[str, Any]:
        raw_dict = params.model_dump(exclude_unset=True)
        results = PreferenceManager.batch_update_preferences(
            profile=profile,
            preferences_dict=raw_dict,
            source_conversation_id=conversation_id
        )
        # Synchronize profile relocation flag if specified
        if params.relocation_allowed is not None:
            profile.willing_to_relocate = params.relocation_allowed
            profile.save(update_fields=['willing_to_relocate'])

        return {
            "status": "success",
            "message": f"Successfully updated {len(results)} preferences.",
            "updated_preferences": results,
            "active_preferences": PreferenceManager.get_user_preferences(profile)
        }

    @classmethod
    def _tool_search_opportunities(cls, params: SearchOpportunitiesSchema, profile: UserProfile) -> Dict[str, Any]:
        filters = {}
        if params.work_mode:
            filters['work_mode'] = params.work_mode
        if params.location:
            filters['location'] = params.location
        if params.exclude_unpaid:
            filters['no_unpaid'] = True

        # Check if user has active dealbreaker against unpaid
        active_prefs = PreferenceManager.get_user_preferences(profile)
        if active_prefs.get('no_unpaid'):
            filters['no_unpaid'] = True

        results = HybridSearchService.search(
            query=params.query,
            filters=filters,
            limit=params.limit or 5
        )

        formatted = [
            {
                "id": str(r['opportunity'].id),
                "title": r['opportunity'].title,
                "company": r['opportunity'].company,
                "location": r['opportunity'].location,
                "work_mode": r['opportunity'].work_mode,
                "stipend": f"{r['opportunity'].currency} {r['opportunity'].min_salary_or_stipend:,.0f} - {r['opportunity'].max_salary_or_stipend:,.0f}",
                "is_unpaid": r['opportunity'].is_unpaid,
                "required_skills": r['opportunity'].required_skills,
                "match_score": r['hybrid_score'],
            }
            for r in results
        ]

        return {
            "query": params.query,
            "result_count": len(formatted),
            "opportunities": formatted
        }

    @classmethod
    def _tool_compare_opportunities(cls, params: CompareOpportunitiesSchema, profile: UserProfile) -> Dict[str, Any]:
        return OpportunityComparisonService.compare(params.opportunity_ids, profile)

    @classmethod
    def _tool_get_user_profile(cls, params: GetUserProfileSchema, profile: UserProfile) -> Dict[str, Any]:
        active_resume = profile.resumes.filter(is_active=True).first()
        skills = []
        if active_resume and params.include_resume:
            skills = list(active_resume.extracted_skills.values_list('name', flat=True))

        return {
            "full_name": profile.full_name,
            "headline": profile.headline,
            "experience_months": profile.experience_months,
            "current_location": profile.current_location,
            "willing_to_relocate": profile.willing_to_relocate,
            "extracted_skills": skills,
            "active_preferences": PreferenceManager.get_user_preferences(profile),
            "dealbreakers": PreferenceManager.get_dealbreakers(profile),
        }

    @classmethod
    def _tool_explain_recommendation(cls, params: ExplainRecommendationSchema, profile: UserProfile) -> Dict[str, Any]:
        try:
            opp = Opportunity.objects.get(id=params.opportunity_id)
        except Opportunity.DoesNotExist:
            return {"error": "Opportunity not found."}

        active_resume = profile.resumes.filter(is_active=True).first()
        candidate_skills = set(active_resume.extracted_skills.values_list('normalized_name', flat=True)) if active_resume else set()
        preferences = PreferenceManager.get_user_preferences(profile)

        eval_res = HybridRecommendationEngine.score_opportunity(
            profile=profile,
            opportunity=opp,
            candidate_skills=candidate_skills,
            preferences=preferences
        )

        return {
            "opportunity_title": opp.title,
            "company": opp.company,
            "overall_match_score": eval_res['overall_score'],
            "passed_hard_filters": eval_res['passed_hard_filters'],
            "exclusion_reasons": eval_res['exclusion_reasons'],
            "matched_skills": eval_res['matched_skills'],
            "missing_skills": eval_res['missing_skills'],
            "score_breakdown": {
                "semantic": eval_res['semantic_score'],
                "skills": eval_res['skill_score'],
                "role": eval_res['role_score'],
                "experience": eval_res['experience_score'],
                "location": eval_res['location_score'],
                "preferences": eval_res['preference_score'],
            }
        }

    @classmethod
    def _tool_identify_skill_gaps(cls, params: IdentifySkillGapsSchema, profile: UserProfile) -> Dict[str, Any]:
        return SkillGapAnalyzer.analyze_candidate_gaps(profile)
