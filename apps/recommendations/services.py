import re
from typing import List, Dict, Any, Tuple, Optional
from decimal import Decimal
from django.db import transaction
from apps.profiles.models import UserProfile
from apps.resumes.models import ExtractedSkill
from apps.opportunities.models import Opportunity, OpportunityEmbedding
from apps.preferences.models import UserPreference
from apps.preferences.services import PreferenceManager
from apps.recommendations.models import Recommendation, RecommendationExplanation
from apps.search.vector_service import VectorEmbeddingService


class HybridRecommendationEngine:
    """
    Deterministic hybrid recommendation engine combining zero-tolerance hard filtering,
    semantic vector similarity, skill graph overlap, and multi-factor weighted scoring.
    """

    DEFAULT_WEIGHTS = {
        'semantic': 0.30,
        'skill': 0.25,
        'role': 0.15,
        'experience': 0.10,
        'location': 0.10,
        'preference': 0.10,
    }

    @classmethod
    def evaluate_hard_filters(
        cls,
        opportunity: Opportunity,
        preferences: Dict[str, Any],
        profile: UserProfile
    ) -> Tuple[bool, List[str]]:
        """
        Phase 1: Deterministic Hard Filter Gate.
        Returns (passed, list_of_violations). A single violation immediately disqualifies the job.
        """
        violations = []

        # 1. Unpaid Opportunity Dealbreaker
        no_unpaid = preferences.get('no_unpaid', False) or preferences.get('exclude_unpaid', False)
        if no_unpaid and opportunity.is_unpaid:
            violations.append("Opportunity is unpaid while candidate prohibits unpaid work.")

        # 2. Excluded Companies
        prohibited_companies = preferences.get('prohibited_companies', [])
        if isinstance(prohibited_companies, list):
            for comp in prohibited_companies:
                if comp.strip().lower() == opportunity.company.strip().lower():
                    violations.append(f"Company '{opportunity.company}' is in candidate's excluded companies list.")

        # 3. Excluded Locations
        excluded_locations = preferences.get('excluded_locations', [])
        if isinstance(excluded_locations, list) and opportunity.work_mode != 'Remote':
            for loc in excluded_locations:
                if loc.strip().lower() in opportunity.location.strip().lower():
                    violations.append(f"Location '{opportunity.location}' is explicitly excluded by candidate.")

        # 4. Mandatory Work Mode Dealbreaker
        required_mode = preferences.get('required_work_mode')
        if required_mode and isinstance(required_mode, str):
            if opportunity.work_mode.lower() != required_mode.lower():
                violations.append(f"Work mode '{opportunity.work_mode}' violates mandatory requirement '{required_mode}'.")

        passed = len(violations) == 0
        return passed, violations

    @classmethod
    def calculate_skill_score(
        cls,
        candidate_skills: set,
        required_skills: List[str],
        preferred_skills: List[str]
    ) -> Tuple[float, List[str], List[str]]:
        """
        Calculates normalized skill match percentage (0-100) and returns (score, matched, missing).
        """
        req_set = {s.strip().lower() for s in required_skills if s.strip()}
        pref_set = {s.strip().lower() for s in preferred_skills if s.strip()}

        if not req_set and not pref_set:
            return 80.0, [], []

        matched_req = candidate_skills.intersection(req_set)
        missing_req = req_set - candidate_skills
        matched_pref = candidate_skills.intersection(pref_set)

        req_ratio = len(matched_req) / len(req_set) if req_set else 1.0
        pref_ratio = len(matched_pref) / len(pref_set) if pref_set else 1.0

        # Required skills hold 75% of skill weight, preferred hold 25%
        score = (0.75 * req_ratio + 0.25 * pref_ratio) * 100.0
        return round(score, 2), sorted(list(matched_req)), sorted(list(missing_req))

    @classmethod
    def calculate_role_score(cls, candidate_roles: List[str], candidate_headline: str, job_title: str) -> float:
        """Calculates role relevance score 0-100 based on token match."""
        title_lower = job_title.lower()
        
        # Check explicit target roles
        for role in candidate_roles:
            if role.lower() in title_lower or title_lower in role.lower():
                return 100.0

        # Check headline tokens
        headline_tokens = set(re.findall(r'\w+', candidate_headline.lower()))
        title_tokens = set(re.findall(r'\w+', title_lower))
        
        if not headline_tokens or not title_tokens:
            return 60.0  # Neutral baseline
            
        overlap = headline_tokens.intersection(title_tokens)
        ratio = len(overlap) / len(title_tokens)
        return round(min(100.0, max(30.0, ratio * 100.0)), 2)

    @classmethod
    def calculate_experience_score(cls, candidate_months: int, min_req_months: int) -> float:
        """Calculates experience compatibility with gradual decay for under-qualification."""
        if candidate_months >= min_req_months:
            return 100.0
        diff = min_req_months - candidate_months
        # Penalty of 20 points per 6 months deficit
        penalty = (diff / 6.0) * 20.0
        return max(0.0, round(100.0 - penalty, 2))

    @classmethod
    def calculate_location_score(
        cls,
        candidate_location: str,
        willing_to_relocate: bool,
        job_location: str,
        job_work_mode: str
    ) -> float:
        """Calculates location score: Remote = 100; Same location = 100; Relocation = 75; Mismatch = 25."""
        if job_work_mode == 'Remote':
            return 100.0
        if candidate_location and candidate_location.lower() in job_location.lower():
            return 100.0
        if willing_to_relocate:
            return 75.0
        return 25.0

    @classmethod
    def calculate_preference_score(cls, opportunity: Opportunity, preferences: Dict[str, Any]) -> float:
        """Evaluates soft preference alignment (work modes, employment types, company size/type)."""
        score = 80.0  # Base satisfaction
        preferred_modes = preferences.get('work_mode', [])
        if preferred_modes:
            if isinstance(preferred_modes, str):
                preferred_modes = [preferred_modes]
            if opportunity.work_mode in preferred_modes:
                score += 15.0
            else:
                score -= 20.0

        if preferences.get('company_preference'):
            comp_pref = str(preferences['company_preference']).lower()
            if 'startup' in comp_pref and ('startup' in opportunity.description.lower() or 'innovative' in opportunity.description.lower()):
                score += 10.0

        return max(0.0, min(100.0, score))

    @classmethod
    def score_opportunity(
        cls,
        profile: UserProfile,
        opportunity: Opportunity,
        candidate_skills: set,
        preferences: Dict[str, Any],
        profile_embedding: Optional[List[float]] = None,
        weights: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        Calculates all sub-scores and the final composite recommendation score.
        """
        w = weights or cls.DEFAULT_WEIGHTS

        # Phase 1: Hard Filters Gate
        passed_filters, violations = cls.evaluate_hard_filters(opportunity, preferences, profile)

        # 1. Semantic Similarity
        semantic_score = 65.0  # Baseline
        if hasattr(opportunity, 'embedding_record') and profile_embedding:
            cosine_sim = VectorEmbeddingService.cosine_similarity_score(
                profile_embedding,
                opportunity.embedding_record.embedding
            )
            semantic_score = round(cosine_sim * 100.0, 2)

        # 2. Skill Match
        skill_score, matched_skills, missing_skills = cls.calculate_skill_score(
            candidate_skills,
            opportunity.required_skills,
            opportunity.preferred_skills
        )

        # 3. Role Relevance
        target_roles = preferences.get('preferred_roles', []) or preferences.get('target_roles', [])
        if not target_roles:
            target_roles = profile.target_roles or []
        role_score = cls.calculate_role_score(target_roles, profile.headline, opportunity.title)

        # 4. Experience Compatibility
        exp_score = cls.calculate_experience_score(profile.experience_months, opportunity.min_experience_months)

        # 5. Location Compatibility
        loc_score = cls.calculate_location_score(
            profile.current_location,
            profile.willing_to_relocate,
            opportunity.location,
            opportunity.work_mode
        )

        # 6. Soft Preference Compatibility
        pref_score = cls.calculate_preference_score(opportunity, preferences)

        # Multi-factor weighted composite score
        composite_score = (
            w['semantic'] * semantic_score +
            w['skill'] * skill_score +
            w['role'] * role_score +
            w['experience'] * exp_score +
            w['location'] * loc_score +
            w['preference'] * pref_score
        )

        # If it failed hard filters, overall score is zeroed or heavily penalized
        final_score = composite_score if passed_filters else 0.0

        return {
            'overall_score': round(final_score, 2),
            'semantic_score': semantic_score,
            'skill_score': skill_score,
            'role_score': role_score,
            'experience_score': exp_score,
            'location_score': loc_score,
            'preference_score': pref_score,
            'passed_hard_filters': passed_filters,
            'exclusion_reasons': violations,
            'matched_skills': matched_skills,
            'missing_skills': missing_skills,
        }

    @classmethod
    @transaction.atomic
    def generate_recommendations_for_user(
        cls,
        profile: UserProfile,
        limit: int = 20,
        recompute: bool = False
    ) -> List[Recommendation]:
        """
        Executes end-to-end recommendation workflow:
        Fetches candidate profile, extracts skills, runs scoring across all active opportunities,
        stores recommendations, and generates grounded explanations.
        """
        # Collect candidate skills from extracted resume records and profile
        active_resume = profile.resumes.filter(is_active=True).first()
        if active_resume:
            skills_qs = active_resume.extracted_skills.values_list('normalized_name', flat=True)
            candidate_skills = {s.lower() for s in skills_qs}
        else:
            candidate_skills = set()

        preferences = PreferenceManager.get_user_preferences(profile)
        
        # Profile embedding for semantic search
        profile_text = f"{profile.headline} {profile.bio} {' '.join(candidate_skills)}"
        profile_emb = VectorEmbeddingService.generate_embedding(profile_text)

        opportunities = Opportunity.objects.filter(is_active=True).select_related('embedding_record')
        
        scored_records = []
        for opp in opportunities:
            eval_res = cls.score_opportunity(
                profile=profile,
                opportunity=opp,
                candidate_skills=candidate_skills,
                preferences=preferences,
                profile_embedding=profile_emb
            )
            scored_records.append((opp, eval_res))

        # Sort: First prioritize passed hard filters, then highest overall score
        scored_records.sort(key=lambda x: (1 if x[1]['passed_hard_filters'] else 0, x[1]['overall_score']), reverse=True)
        top_records = scored_records[:limit]

        saved_recommendations = []
        for opp, res in top_records:
            rec, _ = Recommendation.objects.update_or_create(
                profile=profile,
                opportunity=opp,
                defaults={
                    'overall_score': Decimal(str(res['overall_score'])),
                    'semantic_score': Decimal(str(res['semantic_score'])),
                    'skill_score': Decimal(str(res['skill_score'])),
                    'role_score': Decimal(str(res['role_score'])),
                    'experience_score': Decimal(str(res['experience_score'])),
                    'location_score': Decimal(str(res['location_score'])),
                    'preference_score': Decimal(str(res['preference_score'])),
                    'passed_hard_filters': res['passed_hard_filters'],
                    'exclusion_reasons': res['exclusion_reasons'],
                }
            )

            # Generate grounded factual explanation
            cls._create_explanation(rec, opp, res, profile)
            saved_recommendations.append(rec)

        return saved_recommendations

    @staticmethod
    def _create_explanation(
        rec: Recommendation,
        opp: Opportunity,
        eval_res: Dict[str, Any],
        profile: UserProfile
    ) -> RecommendationExplanation:
        """
        Generates structured and natural language explanation grounded purely in calculated evidence.
        """
        matched = eval_res['matched_skills']
        missing = eval_res['missing_skills']
        pref_matches = []
        concerns = []

        if opp.work_mode == 'Remote':
            pref_matches.append("Remote flexibility matches your work preference.")
        elif profile.current_location and profile.current_location.lower() in opp.location.lower():
            pref_matches.append(f"Located in your primary city ({opp.location}).")

        if opp.is_unpaid:
            concerns.append("This role is unpaid.")
        else:
            pref_matches.append(f"Compensated opportunity ({opp.currency} {opp.min_salary_or_stipend:,.0f} - {opp.max_salary_or_stipend:,.0f}).")

        if missing:
            concerns.append(f"Requires additional skills: {', '.join(missing[:3])}.")

        # Factual summary prose
        skill_summary = f"Strong alignment in {', '.join(matched[:3])}." if matched else "Foundational skill overlap."
        nl_text = (
            f"{opp.title} at {opp.company} is rated at {rec.overall_score}% match. "
            f"{skill_summary} Work mode is {opp.work_mode}. "
        )
        if concerns:
            nl_text += f" Note: {concerns[0]}"

        explanation, _ = RecommendationExplanation.objects.update_or_create(
            recommendation=rec,
            defaults={
                'matched_skills': matched,
                'missing_skills': missing,
                'preference_matches': pref_matches,
                'potential_concerns': concerns,
                'natural_language_explanation': nl_text,
            }
        )
        return explanation


class SkillGapAnalyzer:
    """
    Identifies market-wide skill demands and personalized learning priorities
    based on the actual opportunity corpus.
    """

    @classmethod
    def analyze_candidate_gaps(cls, profile: UserProfile) -> Dict[str, Any]:
        """Calculates frequent skill gaps across opportunities matching candidate's profile."""
        active_resume = profile.resumes.filter(is_active=True).first()
        candidate_skills = set()
        if active_resume:
            candidate_skills = {s.lower() for s in active_resume.extracted_skills.values_list('normalized_name', flat=True)}

        # Analyze top recommended opportunities
        top_recs = Recommendation.objects.filter(profile=profile, passed_hard_filters=True).select_related('opportunity')[:15]
        
        missing_skill_frequency = {}
        for rec in top_recs:
            opp = rec.opportunity
            for req in opp.required_skills:
                norm = req.strip().lower()
                if norm not in candidate_skills:
                    missing_skill_frequency[req] = missing_skill_frequency.get(req, 0) + 1

        sorted_gaps = sorted(missing_skill_frequency.items(), key=lambda x: x[1], reverse=True)
        
        learning_priorities = [
            {
                'skill': skill,
                'demand_count': count,
                'demand_percentage': round((count / max(1, len(top_recs))) * 100, 1),
                'priority': 'HIGH' if count >= 3 else 'MEDIUM'
            }
            for skill, count in sorted_gaps[:8]
        ]

        return {
            'candidate_skills_count': len(candidate_skills),
            'candidate_skills': sorted(list(candidate_skills)),
            'target_opportunities_analyzed': len(top_recs),
            'learning_priorities': learning_priorities,
        }


class OpportunityComparisonService:
    """
    Constructs a comparative matrix for 2-4 opportunities.
    """

    @classmethod
    def compare(cls, opportunity_ids: List[str], profile: UserProfile) -> Dict[str, Any]:
        """Generates side-by-side comparison with match scores and trade-off analysis."""
        opps = Opportunity.objects.filter(id__in=opportunity_ids)
        if not opps.exists():
            return {'error': 'No matching opportunities found'}

        recs = {
            rec.opportunity_id: rec
            for rec in Recommendation.objects.filter(profile=profile, opportunity__in=opps).select_related('explanation')
        }

        comparison_items = []
        for opp in opps:
            rec = recs.get(opp.id)
            score = float(rec.overall_score) if rec else None
            matched = rec.explanation.matched_skills if (rec and hasattr(rec, 'explanation')) else []
            missing = rec.explanation.missing_skills if (rec and hasattr(rec, 'explanation')) else []
            
            comparison_items.append({
                'id': str(opp.id),
                'title': opp.title,
                'company': opp.company,
                'work_mode': opp.work_mode,
                'location': opp.location,
                'employment_type': opp.employment_type,
                'stipend_range': f"{opp.currency} {opp.min_salary_or_stipend:,.0f} - {opp.max_salary_or_stipend:,.0f}",
                'is_unpaid': opp.is_unpaid,
                'match_score': score,
                'required_skills': opp.required_skills,
                'matched_skills': matched,
                'missing_skills': missing,
            })

        return {
            'comparison_count': len(comparison_items),
            'items': comparison_items,
        }
