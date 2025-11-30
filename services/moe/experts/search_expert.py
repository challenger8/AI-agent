"""
services/moe/experts/search_expert.py
-------------------------------------
Expert for semantic search using RAG/CAG
"""

import re
from typing import Any, Dict,List

from ..base_expert import BaseExpert, ExpertResult
from config.moe_settings import MoESettings


class SearchExpert(BaseExpert):
    """Expert specializing in semantic search using RAG/CAG"""

    @property
    def expert_type(self) -> str:
        return 'search'

    @property
    def description(self) -> str:
        return "Performs semantic search across deals, activities, and agents using RAG/CAG"

    @property
    def supported_query_types(self) -> list:
        return ['search', 'find', 'query', 'lookup']

    def can_handle(self, query: str, context: Dict[str, Any] = None) -> float:
        """Determine if this expert can handle the query"""
        query_lower = query.lower()
        score = 0.0

        # Check for search-related keywords
        search_keywords = [
            'find', 'پیدا', 'search', 'جستجو', 'look', 'گشتن', 'query', 'پرس‌وجو',
            'where', 'کجا', 'which', 'کدام', 'related', 'مرتبط', 'similar', 'مشابه',
            'show me', 'نشان بده', 'list', 'لیست', 'get', 'بگیر'
        ]

        for keyword in search_keywords:
            if keyword in query_lower:
                score += 0.15

        # Check for question patterns
        question_patterns = [
            r'^(what|where|which|who|how)\s',
            r'^(چه|کجا|کدام|چگونه)\s',
            r'\?$'
        ]

        for pattern in question_patterns:
            if re.search(pattern, query_lower):
                score += 0.1

        # Context boost
        if context and context.get('search_mode'):
            score += 0.3

        # Default expert boost (search is often the fallback)
        if score < 0.3:
            score = 0.3  # Minimum score for search

        return min(score, 1.0)

    async def analyze(self, query: str, context: Dict[str, Any] = None) -> ExpertResult:
        """Perform semantic search"""
        context = context or {}

        # Try CAG orchestrator first (includes correction)
        cag_orchestrator = self.services.get('cag_orchestrator')
        rag_service = self.services.get('rag_search')

        if cag_orchestrator:
            result = await self._search_with_cag(query, context, cag_orchestrator)
        elif rag_service:
            result = await self._search_with_rag(query, context, rag_service)
        else:
            return ExpertResult.error_result(
                self.expert_type,
                "Search services not available"
            )

        if 'error' in result:
            return ExpertResult(
                expert_type=self.expert_type,
                success=False,
                data=result,
                confidence=0.0,
                reasoning=f"Search failed: {result['error']}"
            )

        confidence = self.calculate_confidence(query, result)

        return ExpertResult(
            expert_type=self.expert_type,
            success=True,
            data=result,
            confidence=confidence,
            reasoning=f"Found {result.get('total_results', 0)} results"
        )

    async def _search_with_cag(
        self,
        query: str,
        context: Dict[str, Any],
        cag_orchestrator
    ) -> Dict[str, Any]:
        """Perform search using CAG orchestrator"""
        try:
            # Get search parameters from context
            n_results = context.get('n_results', 10)
            entity_type = context.get('entity_type', None)

            # Perform CAG search
            result = await cag_orchestrator.search(
                query=query,
                n_results=n_results,
                entity_type=entity_type
            )

            if not result:
                return {
                    'query': query,
                    'total_results': 0,
                    'results': [],
                    'message': 'No results found'
                }

            # Format results
            formatted_results = []
            all_results = result.get('results', {})

            for result_type, items in all_results.items():
                for item in items:
                    formatted_results.append({
                        'type': result_type,
                        'data': item.get('document', item),
                        'score': item.get('score', 0.0),
                        'metadata': item.get('metadata', {})
                    })

            # Sort by score
            formatted_results.sort(key=lambda x: x.get('score', 0), reverse=True)

            return {
                'query': query,
                'total_results': len(formatted_results),
                'results': formatted_results[:n_results],
                'correction_applied': result.get('correction_applied', False),
                'iterations': result.get('iterations', 1),
                'search_type': 'cag'
            }

        except Exception as e:
            return {'error': str(e)}

    async def _search_with_rag(
        self,
        query: str,
        context: Dict[str, Any],
        rag_service
    ) -> Dict[str, Any]:
        """Perform search using RAG service"""
        try:
            # Get search parameters from context
            n_results = context.get('n_results', 10)

            # Perform RAG search
            result = rag_service.search(query=query, n_results=n_results)

            if not result:
                return {
                    'query': query,
                    'total_results': 0,
                    'results': [],
                    'message': 'No results found'
                }

            # Format results
            formatted_results = []
            for result_type, items in result.items():
                if result_type == 'query':
                    continue
                for item in items:
                    formatted_results.append({
                        'type': result_type,
                        'data': item.get('document', item),
                        'score': item.get('score', 0.0),
                        'metadata': item.get('metadata', {})
                    })

            # Sort by score
            formatted_results.sort(key=lambda x: x.get('score', 0), reverse=True)

            return {
                'query': query,
                'total_results': len(formatted_results),
                'results': formatted_results[:n_results],
                'search_type': 'rag'
            }

        except Exception as e:
            return {'error': str(e)}

    @property
    def confidence_boost_keys(self) -> List[str]:
        return ['results', 'matches', 'relevance_scores']

