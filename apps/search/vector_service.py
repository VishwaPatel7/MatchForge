import os
import re
import numpy as np
from typing import List, Dict, Any, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from apps.opportunities.models import Opportunity, OpportunityEmbedding


class VectorEmbeddingService:
    """
    Manages vector representations, cosine similarity computations,
    and semantic search retrieval across opportunities.
    Provides offline deterministic vector modeling with optional OpenAI embedding upgrade.
    """
    DEFAULT_DIMENSIONS = 128
    _vectorizer = None

    @classmethod
    def get_vectorizer(cls) -> TfidfVectorizer:
        """Returns or fits a shared TF-IDF vectorizer across known technical terms."""
        if cls._vectorizer is None:
            # Common technical corpus vocabulary for robust zero-shot feature mapping
            initial_corpus = [
                "python django rest framework backend api database postgresql redis celery docker microservices",
                "frontend react typescript javascript html css redux ui responsive tailwind next.js",
                "machine learning deep learning pytorch tensorflow scikit-learn nlp llm rag computer vision",
                "cloud devops aws kubernetes k8s ci cd linux bash terraform infrastructure gcp azure",
                "software engineer intern backend scalability distributed systems sql data modeling",
                "full stack developer nodejs express react mongodb web development graphql",
                "data engineer spark kafka airflow sql etl data warehouse postgresql snowflake",
                "internship remote bangalore hyderabad pune mumbai delhi gurgaon hybrid onsite stipend salary",
            ]
            cls._vectorizer = TfidfVectorizer(max_features=cls.DEFAULT_DIMENSIONS, stop_words='english')
            cls._vectorizer.fit(initial_corpus)
        return cls._vectorizer

    @classmethod
    def generate_embedding(cls, text: str) -> List[float]:
        """
        Generates a normalized dense vector embedding.
        If OPENAI_API_KEY is configured and requests succeed, uses OpenAI embeddings;
        otherwise uses deterministic normalized TF-IDF vector.
        """
        openai_key = os.getenv('OPENAI_API_KEY', '')
        if openai_key and len(openai_key) > 20:
            try:
                import requests
                headers = {'Authorization': f'Bearer {openai_key}', 'Content-Type': 'application/json'}
                payload = {'input': text[:1000], 'model': 'text-embedding-3-small'}
                resp = requests.post('https://api.openai.com/v1/embeddings', json=payload, headers=headers, timeout=5)
                if resp.status_code == 200:
                    data = resp.json()
                    emb = data['data'][0]['embedding'][:cls.DEFAULT_DIMENSIONS]
                    return emb
            except Exception:
                pass  # Fall back to deterministic vectorizer

        # Deterministic offline vectorizer fallback
        vectorizer = cls.get_vectorizer()
        vec = vectorizer.transform([text]).toarray()[0]
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        else:
            # Hash-based deterministic fallback for out-of-vocabulary queries
            vec = np.zeros(cls.DEFAULT_DIMENSIONS, dtype=np.float32)
            words = text.lower().split()
            for w in words:
                idx = abs(hash(w)) % cls.DEFAULT_DIMENSIONS
                vec[idx] += 1.0
            norm = np.linalg.norm(vec)
            if norm > 0:
                vec = vec / norm
        return vec.tolist()

    @staticmethod
    def cosine_similarity_score(vec1: List[float], vec2: List[float]) -> float:
        """Computes cosine similarity between two vectors, returning 0.0 to 1.0."""
        a = np.array(vec1, dtype=np.float32)
        b = np.array(vec2, dtype=np.float32)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        dot = np.dot(a, b) / (norm_a * norm_b)
        return float(np.clip(dot, 0.0, 1.0))

    @classmethod
    def search_semantic(cls, query: str, limit: int = 10, min_score: float = 0.05) -> List[Tuple[Opportunity, float]]:
        """
        Retrieves top-K opportunities by cosine similarity to the query embedding.
        """
        query_vec = cls.generate_embedding(query)
        embedding_records = OpportunityEmbedding.objects.select_related('opportunity').filter(opportunity__is_active=True)

        scored_results = []
        for rec in embedding_records:
            sim = cls.cosine_similarity_score(query_vec, rec.embedding)
            if sim >= min_score:
                scored_results.append((rec.opportunity, sim))

        scored_results.sort(key=lambda x: x[1], reverse=True)
        return scored_results[:limit]
