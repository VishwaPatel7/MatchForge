import pytest
from apps.resumes.services import ResumeParsingService


class TestResumeIntelligence:
    def test_skill_extraction_taxonomy(self):
        sample_text = """
        Experienced in building scalable microservices using Python, Django, and Django REST Framework.
        Skilled in PostgreSQL database schema design, Redis caching, and Docker containerization.
        Familiar with React, JavaScript, Git, and Linux environments.
        """
        extracted = ResumeParsingService.extract_skills(sample_text)
        skill_names = {s['name'] for s in extracted}
        
        assert 'Python' in skill_names
        assert 'Django' in skill_names
        assert 'Django REST Framework' in skill_names
        assert 'PostgreSQL' in skill_names
        assert 'Redis' in skill_names
        assert 'Docker' in skill_names

    def test_completeness_calculation(self):
        text = "Short text"
        skills = []
        edu = []
        exp = []
        low_score = ResumeParsingService.compute_completeness(text, skills, edu, exp)
        assert low_score < 30.0

        full_text = "Comprehensive resume with substantial background details " * 10
        full_skills = [{'name': 'Python'}, {'name': 'Django'}, {'name': 'PostgreSQL'}]
        full_edu = [{'degree': 'B.Tech ICT'}]
        full_exp = [{'role': 'Backend Developer Intern'}]
        high_score = ResumeParsingService.compute_completeness(full_text, full_skills, full_edu, full_exp)
        assert high_score >= 80.0

    def test_education_and_experience_extraction(self):
        text = """
        Bachelor of Technology in Information and Communication Technology
        DA-IICT 2025
        Software Engineer Intern
        Developed high-throughput APIs for processing payments.
        """
        edu = ResumeParsingService.extract_education(text)
        exp, months = ResumeParsingService.extract_experience(text)
        
        assert len(edu) >= 1
        assert len(exp) >= 1
        assert months > 0
