import hashlib
import io
import re
from typing import Dict, List, Any, Tuple
from pypdf import PdfReader
from apps.resumes.models import CandidateResume, ExtractedSkill
from apps.profiles.models import UserProfile

# Comprehensive Technical Skill Taxonomy
SKILL_TAXONOMY = {
    # Programming Languages
    'python': ('Python', 'LANGUAGE'),
    'javascript': ('JavaScript', 'LANGUAGE'),
    'typescript': ('TypeScript', 'LANGUAGE'),
    'java': ('Java', 'LANGUAGE'),
    'c++': ('C++', 'LANGUAGE'),
    'c#': ('C#', 'LANGUAGE'),
    'golang': ('Go', 'LANGUAGE'),
    'go': ('Go', 'LANGUAGE'),
    'rust': ('Rust', 'LANGUAGE'),
    'ruby': ('Ruby', 'LANGUAGE'),
    'php': ('PHP', 'LANGUAGE'),
    'sql': ('SQL', 'LANGUAGE'),
    'html': ('HTML', 'LANGUAGE'),
    'css': ('CSS', 'LANGUAGE'),
    'bash': ('Bash', 'LANGUAGE'),

    # Frameworks & Libraries
    'django': ('Django', 'FRAMEWORK'),
    'django rest framework': ('Django REST Framework', 'FRAMEWORK'),
    'drf': ('Django REST Framework', 'FRAMEWORK'),
    'flask': ('Flask', 'FRAMEWORK'),
    'fastapi': ('FastAPI', 'FRAMEWORK'),
    'react': ('React', 'FRAMEWORK'),
    'react.js': ('React', 'FRAMEWORK'),
    'vue': ('Vue.js', 'FRAMEWORK'),
    'angular': ('Angular', 'FRAMEWORK'),
    'spring boot': ('Spring Boot', 'FRAMEWORK'),
    'node.js': ('Node.js', 'FRAMEWORK'),
    'nodejs': ('Node.js', 'FRAMEWORK'),
    'express': ('Express.js', 'FRAMEWORK'),
    'pytorch': ('PyTorch', 'FRAMEWORK'),
    'tensorflow': ('TensorFlow', 'FRAMEWORK'),
    'scikit-learn': ('Scikit-Learn', 'FRAMEWORK'),
    'pandas': ('Pandas', 'FRAMEWORK'),
    'numpy': ('NumPy', 'FRAMEWORK'),

    # Databases & Caching
    'postgresql': ('PostgreSQL', 'DATABASE'),
    'postgres': ('PostgreSQL', 'DATABASE'),
    'mysql': ('MySQL', 'DATABASE'),
    'mongodb': ('MongoDB', 'DATABASE'),
    'redis': ('Redis', 'DATABASE'),
    'sqlite': ('SQLite', 'DATABASE'),
    'elasticsearch': ('Elasticsearch', 'DATABASE'),
    'cassandra': ('Cassandra', 'DATABASE'),
    'pgvector': ('pgvector', 'DATABASE'),

    # DevOps, Cloud & Tools
    'docker': ('Docker', 'DEVOPS'),
    'kubernetes': ('Kubernetes', 'DEVOPS'),
    'k8s': ('Kubernetes', 'DEVOPS'),
    'aws': ('AWS', 'DEVOPS'),
    'azure': ('Azure', 'DEVOPS'),
    'gcp': ('Google Cloud Platform', 'DEVOPS'),
    'git': ('Git', 'DEVOPS'),
    'github': ('GitHub', 'DEVOPS'),
    'gitlab': ('GitLab', 'DEVOPS'),
    'ci/cd': ('CI/CD', 'DEVOPS'),
    'celery': ('Celery', 'DEVOPS'),
    'nginx': ('Nginx', 'DEVOPS'),
    'linux': ('Linux', 'DEVOPS'),

    # Architecture & Concepts
    'rest api': ('REST APIs', 'ARCHITECTURE'),
    'restful': ('REST APIs', 'ARCHITECTURE'),
    'graphql': ('GraphQL', 'ARCHITECTURE'),
    'microservices': ('Microservices', 'ARCHITECTURE'),
    'rag': ('RAG', 'ARCHITECTURE'),
    'llm': ('LLMs', 'ARCHITECTURE'),
    'vector search': ('Vector Search', 'ARCHITECTURE'),
    'system design': ('System Design', 'ARCHITECTURE'),
}


class ResumeParsingService:
    """
    Production-grade extraction service that parses PDF resumes, computes checksums,
    extracts structured sections, categorizes technical skills, and computes completeness metrics.
    """

    @staticmethod
    def extract_text_from_pdf(file_bytes: bytes) -> str:
        """Extracts clean text content from a PDF stream using PyPDF."""
        try:
            reader = PdfReader(io.BytesIO(file_bytes))
            text_chunks = []
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text_chunks.append(page_text)
            return "\n\n".join(text_chunks).strip()
        except Exception as e:
            raise ValueError(f"Failed to read PDF document: {str(e)}")

    @staticmethod
    def compute_sha256(file_bytes: bytes) -> str:
        """Computes SHA-256 hash for deduplication."""
        return hashlib.sha256(file_bytes).hexdigest()

    @classmethod
    def extract_skills(cls, text: str) -> List[Dict[str, Any]]:
        """Identifies and normalizes technical skills against the taxonomy."""
        lowered_text = " " + re.sub(r'[^a-zA-Z0-9\+#\.]', ' ', text.lower()) + " "
        found_skills = {}

        # Look for multi-word skills first (e.g., "django rest framework", "spring boot")
        sorted_keys = sorted(SKILL_TAXONOMY.keys(), key=lambda k: len(k), reverse=True)
        for key in sorted_keys:
            pattern = r'(?:\b|\s)' + re.escape(key) + r'(?:\b|\s)'
            if re.search(pattern, lowered_text):
                canonical_name, category = SKILL_TAXONOMY[key]
                norm_key = canonical_name.lower()
                if norm_key not in found_skills:
                    # Estimate proficiency/confidence based on mentions
                    mentions = len(re.findall(pattern, lowered_text))
                    proficiency = min(5, max(1, 2 + mentions))
                    found_skills[norm_key] = {
                        'name': canonical_name,
                        'normalized_name': norm_key,
                        'category': category,
                        'proficiency_level': proficiency,
                        'confidence_score': min(1.0, 0.7 + (mentions * 0.1)),
                    }

        return list(found_skills.values())

    @staticmethod
    def extract_education(text: str) -> List[Dict[str, str]]:
        """Extracts education entries using robust pattern matching."""
        education = []
        edu_keywords = ['b.tech', 'btech', 'bachelor of technology', 'bachelor', 'b.e.', 'm.tech', 'msc', 'master', 'diploma']
        
        lines = text.split('\n')
        for idx, line in enumerate(lines):
            line_lower = line.lower()
            for kw in edu_keywords:
                if kw in line_lower:
                    institution = lines[idx + 1].strip() if idx + 1 < len(lines) else ''
                    education.append({
                        'degree': line.strip()[:150],
                        'institution': institution[:150],
                        'year': re.search(r'\b(20\d{2})\b', line) and re.search(r'\b(20\d{2})\b', line).group(1) or 'Present'
                    })
                    break
        return education[:3]

    @staticmethod
    def extract_experience(text: str) -> Tuple[List[Dict[str, Any]], int]:
        """Extracts internship/work experience and estimates total duration in months."""
        experience = []
        total_months = 0

        # Match job roles & internships
        role_pattern = r'(intern|internship|software engineer|developer|backend|frontend|full stack|trainee)'
        lines = text.split('\n')
        for idx, line in enumerate(lines):
            if re.search(role_pattern, line, re.IGNORECASE):
                snippet = line.strip()
                if len(snippet) > 5 and len(snippet) < 120:
                    experience.append({
                        'role': snippet,
                        'description': lines[idx + 1].strip()[:300] if idx + 1 < len(lines) else '',
                    })
                    total_months += 4  # Estimate ~4 months per listed internship/role

        return experience[:5], min(total_months, 36)

    @staticmethod
    def compute_completeness(text: str, skills: List[Dict], education: List[Dict], experience: List[Dict]) -> float:
        """Calculates resume completeness score 0-100."""
        score = 0.0
        if len(text) > 150:
            score += 20.0  # Basic content
        if len(skills) >= 3:
            score += 30.0  # Skills present
        elif len(skills) > 0:
            score += 15.0
        if education:
            score += 25.0  # Education section
        if experience:
            score += 25.0  # Experience/projects
        return min(100.0, score)

    @classmethod
    def process_resume(cls, resume_instance: CandidateResume) -> CandidateResume:
        """
        Parses resume file, populates database entities, and updates user profile.
        """
        try:
            resume_instance.parsing_status = CandidateResume.STATUS_PROCESSING
            resume_instance.save(update_fields=['parsing_status'])

            file_bytes = resume_instance.file.read()
            resume_instance.file.seek(0)
            
            # 1. Text extraction & hash
            text = cls.extract_text_from_pdf(file_bytes)
            resume_instance.raw_text = text
            resume_instance.file_hash = cls.compute_sha256(file_bytes)
            
            # 2. Extract sections
            skills = cls.extract_skills(text)
            education = cls.extract_education(text)
            experience, estimated_months = cls.extract_experience(text)
            
            resume_instance.education = education
            resume_instance.experience = experience
            resume_instance.completeness_score = cls.compute_completeness(text, skills, education, experience)
            resume_instance.parsing_status = CandidateResume.STATUS_COMPLETED
            resume_instance.save()

            # 3. Save extracted skills
            # Delete previous skills for this resume
            ExtractedSkill.objects.filter(resume=resume_instance).delete()
            skill_records = [
                ExtractedSkill(
                    resume=resume_instance,
                    name=s['name'],
                    normalized_name=s['normalized_name'],
                    category=s['category'],
                    proficiency_level=s['proficiency_level'],
                    confidence_score=s['confidence_score'],
                )
                for s in skills
            ]
            ExtractedSkill.objects.bulk_create(skill_records)

            # 4. Synchronize UserProfile
            profile = resume_instance.profile
            if not profile.headline:
                top_skills = [s['name'] for s in skills[:3]]
                profile.headline = f"Software Engineer ({', '.join(top_skills)})" if top_skills else "Software Engineer"
            
            if estimated_months > profile.experience_months:
                profile.experience_months = estimated_months

            profile.parsed_metadata = {
                'skills_count': len(skills),
                'top_skills': [s['name'] for s in skills[:8]],
                'education_summary': [e.get('degree', '') for e in education],
                'completeness': resume_instance.completeness_score,
            }
            profile.save()

            return resume_instance

        except Exception as e:
            resume_instance.parsing_status = CandidateResume.STATUS_FAILED
            resume_instance.error_message = str(e)
            resume_instance.save(update_fields=['parsing_status', 'error_message'])
            raise e
