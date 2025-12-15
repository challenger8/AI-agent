"""
utils/result_formatter.py
-------------------------
Unified search result formatting utilities.

DRY: Consolidates 150+ lines of duplicate result formatting logic
found across 5 service files:
- services/moe/experts/search_expert.py (2 occurrences)
- services/vector_store_service.py
- services/chromadb_query_optimization.py
- services/rag_search_service.py
"""

from typing import Dict, List, Any, Optional


class SearchResultFormatter:
    """
    Centralized search result formatting for consistent data structures.

    Consolidates duplicate formatting patterns found in:
    - RAG search results
    - CAG search results
    - ChromaDB query results
    - Vector store results
    """

    @staticmethod
    def format_chromadb_results(raw_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Format raw ChromaDB results to standard format.

        DRY: Eliminates duplicate ChromaDB formatting in:
        - services/vector_store_service.py:180-189
        - services/chromadb_query_optimization.py:162-172

        Args:
            raw_results: Raw ChromaDB query results with structure:
                {
                    'ids': [[id1, id2, ...]],
                    'documents': [[doc1, doc2, ...]],
                    'metadatas': [[meta1, meta2, ...]],
                    'distances': [[dist1, dist2, ...]]
                }

        Returns:
            List of formatted results with structure:
                [
                    {
                        'id': str,
                        'text': str,
                        'metadata': dict,
                        'distance': float,
                        'similarity': float  # 1 - distance
                    },
                    ...
                ]
        """
        formatted = []

        # ChromaDB returns nested lists (batched format)
        if raw_results.get('ids') and raw_results['ids'][0]:
            for i, doc_id in enumerate(raw_results['ids'][0]):
                # Safely extract values with defaults
                text = raw_results['documents'][0][i] if raw_results.get('documents') else ''
                metadata = raw_results['metadatas'][0][i] if raw_results.get('metadatas') else {}
                distance = raw_results['distances'][0][i] if raw_results.get('distances') else 0

                formatted.append({
                    'id': doc_id,
                    'text': text,
                    'metadata': metadata,
                    'distance': distance,
                    'similarity': 1 - distance if distance else 0
                })

        return formatted

    @staticmethod
    def format_typed_results(
        results: Dict[str, List],
        skip_keys: Optional[List[str]] = None,
        sort_by_score: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Format dictionary of typed results (deals, activities, etc).

        DRY: Eliminates duplicate formatting in:
        - services/moe/experts/search_expert.py:104-117 (CAG results)
        - services/moe/experts/search_expert.py:154-167 (RAG results)

        Args:
            results: Dictionary with structure:
                {
                    'deals': [item1, item2, ...],
                    'activities': [item1, item2, ...],
                    ...
                }
            skip_keys: List of keys to skip (e.g., ['query', 'metadata'])
            sort_by_score: Whether to sort results by score (default: True)

        Returns:
            List of formatted results with structure:
                [
                    {
                        'type': str,  # e.g., 'deals', 'activities'
                        'data': dict,
                        'score': float,
                        'metadata': dict
                    },
                    ...
                ]
        """
        skip_keys = skip_keys or []
        formatted_results = []

        for result_type, items in results.items():
            # Skip specified keys
            if result_type in skip_keys:
                continue

            # Handle both list and dict items
            if not isinstance(items, list):
                continue

            for item in items:
                formatted_results.append({
                    'type': result_type,
                    'data': item.get('document', item) if isinstance(item, dict) else item,
                    'score': item.get('score', 0.0) if isinstance(item, dict) else 0.0,
                    'metadata': item.get('metadata', {}) if isinstance(item, dict) else {}
                })

        # Sort by score (highest first)
        if sort_by_score:
            formatted_results.sort(key=lambda x: x.get('score', 0), reverse=True)

        return formatted_results

    @staticmethod
    def format_collection_results(
        results: List[Dict],
        result_type: str,
        round_scores: bool = True,
        decimal_places: int = 4
    ) -> List[Dict[str, Any]]:
        """
        Format collection search results with type annotation.

        DRY: Eliminates duplicate formatting in:
        - services/rag_search_service.py:314-323

        Args:
            results: List of raw search results
            result_type: Type annotation (e.g., 'deal', 'activity')
            round_scores: Whether to round similarity/distance scores
            decimal_places: Number of decimal places for rounding

        Returns:
            List of formatted results with structure:
                [
                    {
                        'id': str,
                        'type': str,
                        'text': str,
                        'metadata': dict,
                        'similarity_score': float,
                        'distance': float
                    },
                    ...
                ]
        """
        formatted = []

        for result in results:
            similarity = result.get('similarity', 0)
            distance = result.get('distance', 0)

            # Round if requested
            if round_scores:
                similarity = round(similarity, decimal_places)
                distance = round(distance, decimal_places)

            formatted.append({
                'id': result.get('id'),
                'type': result_type,
                'text': result.get('text'),
                'metadata': result.get('metadata', {}),
                'similarity_score': similarity,
                'distance': distance
            })

        return formatted

    @staticmethod
    def format_hybrid_results(
        chromadb_results: Dict[str, Any] = None,
        typed_results: Dict[str, List] = None,
        collection_results: List[Dict] = None,
        limit: int = None
    ) -> Dict[str, Any]:
        """
        Format hybrid search results combining multiple sources.

        Convenience method for formatting results from multiple search strategies.

        Args:
            chromadb_results: Raw ChromaDB results (if any)
            typed_results: Typed results dict (if any)
            collection_results: Collection results list (if any)
            limit: Limit total results returned

        Returns:
            Dictionary with formatted results and metadata:
                {
                    'total_results': int,
                    'results': List[Dict],
                    'sources': List[str]
                }
        """
        all_results = []
        sources = []

        if chromadb_results:
            all_results.extend(
                SearchResultFormatter.format_chromadb_results(chromadb_results)
            )
            sources.append('chromadb')

        if typed_results:
            all_results.extend(
                SearchResultFormatter.format_typed_results(typed_results)
            )
            sources.append('typed')

        if collection_results:
            all_results.extend(collection_results)
            sources.append('collection')

        # Apply limit if specified
        if limit:
            all_results = all_results[:limit]

        return {
            'total_results': len(all_results),
            'results': all_results,
            'sources': sources
        }
