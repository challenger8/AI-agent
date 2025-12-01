"""
services/rag_search_service.py
------------------------------
RAG (Retrieval-Augmented Generation) search service
Orchestrates semantic search across CRM data
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from services.base_service import BaseService
from services.embedding_service import EmbeddingService
from services.vector_store_service import VectorStoreService
from utils.exceptions import ServiceError


class RAGSearchService(BaseService):
    """Service for semantic search and RAG operations"""
    
    def __init__(self, repositories=None):
        """
        Initialize RAG search service
        
        Args:
            repositories: Repository manager
        """
        super().__init__(repositories)
        self.embedding_service = None
        self.vector_store_service = None
        self.logger = logging.getLogger(__name__)
        self._initialized = False
    
    async def initialize(self):
        """Initialize embedding and vector store services"""
        success = await self._safe_initialize(
            self._setup_rag_services,
            service_name="RAG Search Service",
            raise_on_error=True
        )
        # _initialized is set in _setup_rag_services
        if not success:
            self._initialized = False
    
    async def _setup_rag_services(self):
        """Actual RAG services setup logic"""
        # Initialize embedding service
        self.embedding_service = EmbeddingService(self.repositories)
        await self.embedding_service.initialize()
        self.logger.info("✅ Embedding service initialized")
        
        # Initialize vector store service
        self.vector_store_service = VectorStoreService(self.repositories)
        await self.vector_store_service.initialize()
        self.logger.info("✅ Vector store service initialized")
        
        self._initialized = True
    def _check_initialized(self):
        """Check if service is initialized"""
        if not self._initialized:
            raise ServiceError("RAG search service not initialized. Call initialize() first.")
    
    async def index_all_data(self) -> Dict[str, Any]:
        """
        Index all CRM data into vector store
        
        Returns:
            Indexing summary
        """
        try:
            self._check_initialized()
            self.logger.info("Starting full data indexing...")
            
            # Add all embeddings to vector store
            results = self.vector_store_service.add_all_embeddings(self.embedding_service)
            
            # Get stats
            stats = self.vector_store_service.get_all_stats()
            
            summary = {
                'status': 'success',
                'indexing_results': results,
                'vector_store_stats': stats,
                'timestamp': datetime.now().isoformat()
            }
            
            self.logger.info(f"Indexing complete: {stats['total_documents']} documents indexed")
            return summary
        except Exception as e:
            self.logger.error(f"Indexing failed: {e}")
            raise ServiceError(f"Failed to index data: {e}")
    
    def search(self, query: str, n_results: int = 5) -> Dict[str, Any]:
        """
        Search across all CRM data
        
        Args:
            query: Search query
            n_results: Number of results per collection
            
        Returns:
            Search results organized by type
        """
        try:
            self._check_initialized()
            self.logger.debug(f"Searching for: '{query}' (n_results={n_results})")
            
            # Search all collections
            results = self.vector_store_service.search_all_collections(query, n_results)
            
            # Format response
            formatted_results = self._format_search_results(results)
            
            return {
                'status': 'success',
                'query': query,
                'results': formatted_results,
                'total_matches': sum(len(r) for r in formatted_results.values()),
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Search failed: {e}")
            return {
                'status': 'error',
                'query': query,
                'error': str(e),
                'results': {'deals': [], 'activities': [], 'agents': []},
                'total_matches': 0,
                'timestamp': datetime.now().isoformat()
            }
    
    def search_deals(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """
        Search only in deals
        
        Args:
            query: Search query
            n_results: Number of results
            
        Returns:
            List of matching deals
        """
        try:
            self._check_initialized()
            results = self.vector_store_service.search(query, 'deals', n_results)
            return self._format_collection_results(results, 'deal')
        except Exception as e:
            self.logger.error(f"Deal search failed: {e}")
            return []
    
    def search_activities(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """
        Search only in activities
        
        Args:
            query: Search query
            n_results: Number of results
            
        Returns:
            List of matching activities
        """
        try:
            self._check_initialized()
            results = self.vector_store_service.search(query, 'activities', n_results)
            return self._format_collection_results(results, 'activity')
        except Exception as e:
            self.logger.error(f"Activity search failed: {e}")
            return []
    
    def search_agents(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """
        Search only in agents
        
        Args:
            query: Search query
            n_results: Number of results
            
        Returns:
            List of matching agents
        """
        try:
            self._check_initialized()
            results = self.vector_store_service.search(query, 'agents', n_results)
            return self._format_collection_results(results, 'agent')
        except Exception as e:
            self.logger.error(f"Agent search failed: {e}")
            return []
    
    def search_with_filters(self, query: str, filters: Dict[str, Any] = None, 
                           n_results: int = 5) -> Dict[str, Any]:
        """
        Search with optional metadata filters
        
        Args:
            query: Search query
            filters: Metadata filter conditions (ChromaDB where clause format)
            n_results: Number of results per collection
            
        Returns:
            Filtered search results
        """
        try:
            self._check_initialized()
            self.logger.debug(f"Filtered search: '{query}' with filters: {filters}")
            
            results = {}
            if filters:
                results['deals'] = self.vector_store_service.search(query, 'deals', n_results, filters)
                results['activities'] = self.vector_store_service.search(query, 'activities', n_results, filters)
                results['agents'] = self.vector_store_service.search(query, 'agents', n_results, filters)
            else:
                results = self.vector_store_service.search_all_collections(query, n_results)
            
            formatted_results = self._format_search_results(results)
            
            return {
                'status': 'success',
                'query': query,
                'filters': filters,
                'results': formatted_results,
                'total_matches': sum(len(r) for r in formatted_results.values()),
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Filtered search failed: {e}")
            return {
                'status': 'error',
                'query': query,
                'filters': filters,
                'error': str(e),
                'results': {'deals': [], 'activities': [], 'agents': []},
                'total_matches': 0,
                'timestamp': datetime.now().isoformat()
            }
    
    def reindex_collection(self, collection_type: str) -> Dict[str, Any]:
        """
        Reindex a specific collection (useful for updates)
        
        Args:
            collection_type: 'deals', 'activities', or 'agents'
            
        Returns:
            Reindexing status
        """
        try:
            self._check_initialized()
            
            if collection_type not in ['deals', 'activities', 'agents']:
                raise ServiceError(f"Invalid collection type: {collection_type}")
            
            self.logger.info(f"Reindexing {collection_type}...")
            
            # Delete old collection
            self.vector_store_service.delete_collection(collection_type)
            self.logger.info(f"Deleted old {collection_type} collection")
            
            # Generate new embeddings
            if collection_type == 'deals':
                embeddings = self.embedding_service.embed_deals()
            elif collection_type == 'activities':
                embeddings = self.embedding_service.embed_activities()
            else:  # agents
                embeddings = self.embedding_service.embed_agents()
            
            # Add to vector store
            self.vector_store_service.add_embeddings(embeddings, collection_type)
            
            stats = self.vector_store_service.get_collection_stats(collection_type)
            
            self.logger.info(f"Reindexing {collection_type} complete: {stats['document_count']} documents")
            
            return {
                'status': 'success',
                'collection': collection_type,
                'stats': stats,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Reindexing {collection_type} failed: {e}")
            raise ServiceError(f"Failed to reindex {collection_type}: {e}")
    
    def get_index_stats(self) -> Dict[str, Any]:
        """
        Get statistics about indexed data
        
        Returns:
            Index statistics
        """
        try:
            self._check_initialized()
            stats = self.vector_store_service.get_all_stats()
            return {
                'status': 'success',
                'stats': stats,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Failed to get stats: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def _format_search_results(self, results: Dict[str, List[Dict]]) -> Dict[str, List[Dict]]:
        """
        Format search results for response
        
        Args:
            results: Raw search results from vector store
            
        Returns:
            Formatted results
        """
        return {
            'deals': self._format_collection_results(results.get('deals', []), 'deal'),
            'activities': self._format_collection_results(results.get('activities', []), 'activity'),
            'agents': self._format_collection_results(results.get('agents', []), 'agent')
        }
    
    def _format_collection_results(self, results: List[Dict], result_type: str) -> List[Dict[str, Any]]:
        """
        Format individual collection results
        
        Args:
            results: Results from collection
            result_type: Type of result ('deal', 'activity', 'agent')
            
        Returns:
            Formatted results
        """
        formatted = []
        for result in results:
            formatted.append({
                'id': result.get('id'),
                'type': result_type,
                'text': result.get('text'),
                'metadata': result.get('metadata', {}),
                'similarity_score': round(result.get('similarity', 0), 4),
                'distance': round(result.get('distance', 0), 4)
            })
        return formatted