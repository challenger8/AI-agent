"""
services/batch_search_service.py
-------------------------------
Batch search service for concurrent query processing
Search multiple queries in parallel instead of sequential
5x faster for multiple searches
"""

import logging
import asyncio
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

from utils.exceptions import ServiceError


class BatchSearchService:
    """Service for batch searching multiple queries concurrently"""
    
    def __init__(self, rag_service, max_workers: int = 5):
        """
        Initialize batch search service
        
        Args:
            rag_service: RAGSearchService instance
            max_workers: Maximum concurrent searches (5 default)
        """
        self.logger = logging.getLogger(__name__)
        self.rag_service = rag_service
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.batch_stats = {
            'total_batches': 0,
            'total_queries': 0,
            'total_time': 0
        }
    
    def search_batch(self, queries: List[str], search_type: str = "all", 
                    n_results: int = 5) -> Dict[str, Any]:
        """
        Search multiple queries concurrently
        
        Args:
            queries: List of search queries
            search_type: Type of search (all/deals/activities/agents)
            n_results: Number of results per query
            
        Returns:
            Dictionary with all results
        """
        try:
            start_time = datetime.now()
            
            self.logger.info(f"Starting batch search: {len(queries)} queries")
            
            # Create futures for concurrent execution
            futures = []
            for query in queries:
                future = self.executor.submit(
                    self._execute_search,
                    query,
                    search_type,
                    n_results
                )
                futures.append((query, future))
            
            # Collect results
            results = {}
            for query, future in futures:
                try:
                    result = future.result(timeout=30)
                    results[query] = result
                except Exception as e:
                    self.logger.error(f"Error searching '{query}': {e}")
                    results[query] = {'error': str(e)}
            
            # Calculate stats
            elapsed = (datetime.now() - start_time).total_seconds()
            self._update_stats(len(queries), elapsed)
            
            self.logger.info(
                f"✅ Batch search complete: "
                f"{len(queries)} queries in {elapsed:.2f}s "
                f"({len(queries)/elapsed:.1f} queries/sec)"
            )
            
            return {
                'status': 'success',
                'queries': len(queries),
                'results': results,
                'time_seconds': round(elapsed, 2),
                'queries_per_second': round(len(queries) / elapsed, 2)
            }
            
        except Exception as e:
            self.logger.error(f"Batch search failed: {e}")
            raise ServiceError(f"Batch search failed: {e}")
    
    def _execute_search(self, query: str, search_type: str, n_results: int) -> Dict[str, Any]:
        """
        Execute single search (called in thread pool)
        
        Args:
            query: Search query
            search_type: Type of search
            n_results: Number of results
            
        Returns:
            Search result
        """
        try:
            if search_type == 'deals':
                results = self.rag_service.search_deals(query, n_results)
            elif search_type == 'activities':
                results = self.rag_service.search_activities(query, n_results)
            elif search_type == 'agents':
                results = self.rag_service.search_agents(query, n_results)
            else:
                return self.rag_service.search(query, n_results)
            
            return {
                'status': 'success',
                'query': query,
                'results': results,
                'count': len(results)
            }
        except Exception as e:
            return {
                'status': 'error',
                'query': query,
                'error': str(e)
            }
    
    def search_deals_batch(self, queries: List[str], n_results: int = 5) -> Dict[str, Any]:
        """Search multiple deal queries"""
        return self.search_batch(queries, 'deals', n_results)
    
    def search_activities_batch(self, queries: List[str], n_results: int = 5) -> Dict[str, Any]:
        """Search multiple activity queries"""
        return self.search_batch(queries, 'activities', n_results)
    
    def search_agents_batch(self, queries: List[str], n_results: int = 5) -> Dict[str, Any]:
        """Search multiple agent queries"""
        return self.search_batch(queries, 'agents', n_results)
    
    def _update_stats(self, query_count: int, elapsed_seconds: float):
        """Update batch statistics"""
        self.batch_stats['total_batches'] += 1
        self.batch_stats['total_queries'] += query_count
        self.batch_stats['total_time'] += elapsed_seconds
    
    def get_stats(self) -> Dict[str, Any]:
        """Get batch search statistics"""
        avg_queries_per_batch = (
            self.batch_stats['total_queries'] / self.batch_stats['total_batches']
            if self.batch_stats['total_batches'] > 0
            else 0
        )
        
        avg_time_per_query = (
            self.batch_stats['total_time'] / self.batch_stats['total_queries']
            if self.batch_stats['total_queries'] > 0
            else 0
        )
        
        return {
            'total_batches': self.batch_stats['total_batches'],
            'total_queries': self.batch_stats['total_queries'],
            'total_time': round(self.batch_stats['total_time'], 2),
            'avg_queries_per_batch': round(avg_queries_per_batch, 1),
            'avg_time_per_query': round(avg_time_per_query * 1000, 2),  # in ms
            'queries_per_second': round(
                self.batch_stats['total_queries'] / self.batch_stats['total_time'], 2
            ) if self.batch_stats['total_time'] > 0 else 0,
            'max_workers': self.max_workers
        }
    
    def shutdown(self):
        """Shutdown thread pool"""
        self.executor.shutdown(wait=True)
        self.logger.info("✅ Batch search service shut down")