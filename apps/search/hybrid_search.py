from typing import List, Dict, Any, Optional
from django.db.models import Q
from apps.opportunities.models import Opportunity
from apps.search.vector_service import VectorEmbeddingService


class HybridSearchService:
    """
    Combines dense semantic vector retrieval with sparse keyword search and metadata filtering.
    """

    @classmethod
    def keyword_search(cls, query: str, filters: Optional[Dict[str, Any]] = None, limit: int = 50) -> List[Opportunity]:
        """Performs structured keyword and metadata search."""
        qs = Opportunity.objects.filter(is_active=True)
        
        if query:
            tokens = [t.strip() for t in query.split() if len(t.strip()) > 1]
            q_obj = Q()
            for token in tokens:
                q_obj |= (
                    Q(title__icontains=token) |
                    Q(company__icontains=token) |
                    Q(description__icontains=token) |
                    Q(location__icontains=token)
                )
            qs = qs.filter(q_obj)

        if filters:
            if filters.get('work_mode'):
                modes = filters['work_mode'] if isinstance(filters['work_mode'], list) else [filters['work_mode']]
                qs = qs.filter(work_mode__in=modes)
            if filters.get('employment_type'):
                types = filters['employment_type'] if isinstance(filters['employment_type'], list) else [filters['employment_type']]
                qs = qs.filter(employment_type__in=types)
            if filters.get('no_unpaid') or filters.get('exclude_unpaid'):
                qs = qs.filter(is_unpaid=False)
            if filters.get('location'):
                qs = qs.filter(location__icontains=filters['location'])

        return list(qs[:limit])

    @classmethod
    def search(
        cls,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 15,
        alpha: float = 0.6  # 0.6 semantic weight, 0.4 keyword weight
    ) -> List[Dict[str, Any]]:
        """
        Executes hybrid retrieval:
        Combines semantic similarity scores with keyword relevance and applies metadata constraints.
        """
        filters = filters or {}
        
        # 1. Semantic search
        semantic_results = VectorEmbeddingService.search_semantic(query, limit=limit * 2)
        semantic_map = {opp.id: (opp, sim) for opp, sim in semantic_results}
        
        # 2. Keyword search
        keyword_results = cls.keyword_search(query, filters=filters, limit=limit * 2)
        keyword_map = {opp.id: opp for opp in keyword_results}
        
        # 3. Candidate pool union
        all_ids = set(semantic_map.keys()).union(set(keyword_map.keys()))
        
        if not all_ids:
            # Fallback to filtered active opportunities respecting all hard constraints
            base_qs = Opportunity.objects.filter(is_active=True)
            if filters.get('no_unpaid') or filters.get('exclude_unpaid'):
                base_qs = base_qs.filter(is_unpaid=False)
            if filters.get('work_mode'):
                modes = filters['work_mode'] if isinstance(filters['work_mode'], list) else [filters['work_mode']]
                base_qs = base_qs.filter(work_mode__in=modes)
            if filters.get('location'):
                base_qs = base_qs.filter(location__icontains=filters['location'])

            base_opps = base_qs[:limit]
            return [
                {
                    'opportunity': opp,
                    'hybrid_score': 50.0,
                    'semantic_score': 0.5,
                    'keyword_match': False,
                }
                for opp in base_opps
            ]

        # Fetch full opportunity objects
        opportunities = {opp.id: opp for opp in Opportunity.objects.filter(id__in=all_ids, is_active=True)}
        
        ranked_items = []
        for opp_id, opp in opportunities.items():
            # Check hard filter constraints
            if (filters.get('no_unpaid') or filters.get('exclude_unpaid')) and opp.is_unpaid:
                continue
            if filters.get('work_mode'):
                modes = filters['work_mode'] if isinstance(filters['work_mode'], list) else [filters['work_mode']]
                if opp.work_mode not in modes:
                    continue

            sem_score = semantic_map.get(opp_id, (opp, 0.0))[1]
            has_kw = opp_id in keyword_map
            kw_score = 1.0 if has_kw else 0.0
            
            hybrid_score = (alpha * sem_score + (1 - alpha) * kw_score) * 100.0
            
            ranked_items.append({
                'opportunity': opp,
                'hybrid_score': round(hybrid_score, 2),
                'semantic_score': round(sem_score * 100, 2),
                'keyword_match': has_kw,
            })

        ranked_items.sort(key=lambda x: x['hybrid_score'], reverse=True)
        return ranked_items[:limit]
