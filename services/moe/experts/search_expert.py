"""
services/moe/experts/search_expert.py
-------------------------------------
Expert for semantic search using RAG/CAG.
REFACTORED: Uses centralized KeywordMatcher for can_handle().
"""

from typing import Any, Dict, List

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
        """
        Determine if this expert can handle the query.

        Uses centralized KeywordMatcher for consistent scoring.
        Search expert has a minimum score of 0.3 (fallback expert).
        """
        matcher = self._get_keyword_matcher()
        return matcher.calculate_score(query, context)

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

