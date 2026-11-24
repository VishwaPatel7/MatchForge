import pytest
from django.contrib.auth.models import User
from apps.profiles.models import UserProfile
from apps.opportunities.models import Opportunity, OpportunityEmbedding
from apps.recommendations.services import HybridRecommendationEngine
from apps.search.vector_service import VectorEmbeddingService
from apps.search.hybrid_search import HybridSearchService


@pytest.mark.django_db
class TestSearchAndRankingEngine:
    def test_cosine_similarity_computation(self):
        v1 = [1.0, 0.0, 0.0]
        v2 = [1.0, 0.0, 0.0]
        v3 = [0.0, 1.0, 0.0]

        assert VectorEmbeddingService.cosine_similarity_score(v1, v2) == pytest.approx(1.0, rel=1e-3)
        assert VectorEmbeddingService.cosine_similarity_score(v1, v3) == pytest.approx(0.0, rel=1e-3)

    def test_hard_filter_unpaid_dealbreaker_enforcement(self):
        user = User.objects.create_user(username='filter_user', password='pass')
        profile = UserProfile.objects.create(user=user, headline='Python Developer')

        unpaid_job = Opportunity.objects.create(
            title='Unpaid Research Intern',
            company='Research Lab',
            description='Unpaid academic exploration',
            work_mode='Remote',
            is_unpaid=True,
            required_skills=['Python']
        )

        # Case 1: Candidate prohibits unpaid work
        passed, violations = HybridRecommendationEngine.evaluate_hard_filters(
            unpaid_job,
            preferences={'no_unpaid': True},
            profile=profile
        )
        assert passed is False
        assert len(violations) >= 1
        assert "unpaid" in violations[0].lower()

        # Score calculation must zero-out
        res = HybridRecommendationEngine.score_opportunity(
            profile=profile,
            opportunity=unpaid_job,
            candidate_skills={'python'},
            preferences={'no_unpaid': True}
        )
        assert res['passed_hard_filters'] is False
        assert res['overall_score'] == 0.0

    def test_reproducible_ranking_scores(self):
        user = User.objects.create_user(username='rank_user', password='pass')
        profile = UserProfile.objects.create(
            user=user,
            headline='Backend Developer',
            current_location='Bangalore',
            experience_months=12
        )

        job = Opportunity.objects.create(
            title='Backend Developer Intern',
            company='Elip AI',
            description='Build scalable APIs with Python and Django',
            location='Bangalore',
            work_mode='Remote',
            is_unpaid=False,
            min_salary_or_stipend=30000,
            max_salary_or_stipend=45000,
            required_skills=['Python', 'Django'],
            preferred_skills=['PostgreSQL', 'Redis']
        )

        res = HybridRecommendationEngine.score_opportunity(
            profile=profile,
            opportunity=job,
            candidate_skills={'python', 'django', 'postgresql'},
            preferences={'no_unpaid': True, 'preferred_roles': ['Backend Developer Intern']}
        )

        assert res['passed_hard_filters'] is True
        assert res['overall_score'] >= 80.0
        assert 'python' in res['matched_skills']
        assert 'django' in res['matched_skills']

    def test_hybrid_search_query(self):
        Opportunity.objects.create(
            title='Platform DevOps Engineer',
            company='CloudCore',
            description='Managing Kubernetes clusters and Docker images',
            location='Remote',
            work_mode='Remote',
            is_unpaid=False,
            required_skills=['Docker', 'Kubernetes']
        )

        results = HybridSearchService.search(query='Kubernetes Docker containerization', limit=5)
        assert len(results) > 0
        top_job = results[0]['opportunity']
        assert 'DevOps' in top_job.title or 'Cloud' in top_job.company or 'Kubernetes' in top_job.description
