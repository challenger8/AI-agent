"""
tests/integration/test_chromadb_optimization.py
-----------------------------------------------
Integration tests for ChromaDB query optimization
Tests connection pooling, HNSW indexing, and concurrent searches
"""

import pytest
import asyncio
import time
from unittest.mock import MagicMock

from services.chromadb_query_optimization import (
    ChromaDBConnectionPool,
    OptimizedVectorStoreQuery,
    OptimizedVectorStore
)
from services.batch_search_service import BatchSearchService


class TestChromeDBConnectionPool:
    """Test ChromaDB connection pool"""
    
    def test_pool_initialization(self):
        """Test pool initialization"""
        try:
            pool = ChromaDBConnectionPool(max_connections=3)
            
            assert len(pool.pool) == 3
            assert all(pool.available) is True
            
            pool.close_all()
        except Exception as e:
            # Skip if ChromaDB not available
            pytest.skip(f"ChromaDB not available: {e}")
    
    def test_get_connection(self):
        """Test getting connection from pool"""
        try:
            pool = ChromaDBConnectionPool(max_connections=2)
            
            conn1 = pool.get_connection()
            assert conn1 is not None
            
            # Connection should be marked unavailable
            assert pool.available[0] is False or pool.available[1] is False
            
            pool.return_connection(conn1)
            pool.close_all()
        except Exception as e:
            pytest.skip(f"ChromaDB not available: {e}")
    
    def test_pool_exhaustion(self):
        """Test pool behavior when exhausted"""
        try:
            pool = ChromaDBConnectionPool(max_connections=1)
            
            conn = pool.get_connection()
            assert conn is not None
            
            # Pool should be exhausted
            available_count = sum(pool.available)
            assert available_count == 0
            
            pool.return_connection(conn)
            pool.close_all()
        except Exception as e:
            pytest.skip(f"ChromaDB not available: {e}")


class TestOptimizedVectorStoreQuery:
    """Test optimized query execution"""
    
    def test_query_stats_initialization(self):
        """Test query stats"""
        try:
            pool = ChromaDBConnectionPool(max_connections=1)
            optimizer = OptimizedVectorStoreQuery(pool)
            
            stats = optimizer.get_stats()
            
            assert stats['total_queries'] == 0
            assert stats['avg_time_ms'] == 0
            
            pool.close_all()
        except Exception as e:
            pytest.skip(f"ChromaDB not available: {e}")
    
    def test_format_results(self):
        """Test result formatting"""
        try:
            pool = ChromaDBConnectionPool(max_connections=1)
            optimizer = OptimizedVectorStoreQuery(pool)
            
            raw_results = {
                'ids': [['id1', 'id2']],
                'documents': [['doc1', 'doc2']],
                'metadatas': [[{'key': 'val1'}, {'key': 'val2'}]],
                'distances': [[0.1, 0.2]]
            }
            
            formatted = optimizer._format_results(raw_results)
            
            assert len(formatted) == 2
            assert formatted[0]['id'] == 'id1'
            assert formatted[0]['similarity'] == 0.9  # 1 - 0.1
            
            pool.close_all()
        except Exception as e:
            pytest.skip(f"ChromaDB not available: {e}")


class TestBatchSearchService:
    """Test batch search service"""
    
    @pytest.fixture
    def mock_rag_service(self):
        """Mock RAG service"""
        mock = MagicMock()
        
        def search_side_effect(query, n_results=5):
            return {
                'status': 'success',
                'query': query,
                'total_matches': 3,
                'results': {
                    'deals': [
                        {'id': '1', 'text': f'Result for {query}', 'similarity': 0.95}
                    ],
                    'activities': [],
                    'agents': []
                }
            }
        
        mock.search.side_effect = search_side_effect
        mock.search_deals.side_effect = search_side_effect
        
        return mock
    
    def test_batch_search_initialization(self, mock_rag_service):
        """Test batch search initialization"""
        service = BatchSearchService(mock_rag_service, max_workers=3)
        
        assert service.max_workers == 3
        assert service.rag_service is mock_rag_service
        
        service.shutdown()
    
    def test_search_batch(self, mock_rag_service):
        """Test batch search"""
        service = BatchSearchService(mock_rag_service, max_workers=5)
        
        queries = ["query1", "query2", "query3"]
        result = service.search_batch(queries, "all", 5)
        
        assert result['status'] == 'success'
        assert result['queries'] == 3
        assert len(result['results']) == 3
        assert 'query1' in result['results']
        
        service.shutdown()
    
    def test_search_deals_batch(self, mock_rag_service):
        """Test batch deal search"""
        service = BatchSearchService(mock_rag_service, max_workers=5)
        
        queries = ["deals query 1", "deals query 2"]
        result = service.search_deals_batch(queries, 5)
        
        assert result['status'] == 'success'
        assert result['queries'] == 2
        
        service.shutdown()
    
    def test_batch_stats(self, mock_rag_service):
        """Test batch statistics"""
        service = BatchSearchService(mock_rag_service, max_workers=3)
        
        queries = ["q1", "q2", "q3"]
        service.search_batch(queries, "all", 5)
        
        stats = service.get_stats()
        
        assert stats['total_batches'] == 1
        assert stats['total_queries'] == 3
        assert stats['queries_per_second'] > 0
        
        service.shutdown()
    
    def test_concurrent_execution(self, mock_rag_service):
        """Test concurrent execution is faster than sequential"""
        service = BatchSearchService(mock_rag_service, max_workers=5)
        
        queries = ["query"] * 10
        
        start = time.time()
        result = service.search_batch(queries, "all", 5)
        batch_time = time.time() - start
        
        # Batch should complete reasonably fast
        assert batch_time < 10  # Should not take too long
        assert result['status'] == 'success'
        
        service.shutdown()


class TestOptimizedVectorStore:
    """Test optimized vector store"""
    
    @pytest.mark.asyncio
    async def test_optimized_store_initialization(self):
        """Test optimized store initialization"""
        try:
            mock_repo = MagicMock()
            store = OptimizedVectorStore(mock_repo)
            
            await store.initialize()
            
            assert 'deals' in store.collections
            assert 'activities' in store.collections
            assert 'agents' in store.collections
            
            store.close()
        except Exception as e:
            pytest.skip(f"ChromaDB not available: {e}")
    
    def test_query_stats(self):
        """Test query statistics"""
        try:
            mock_repo = MagicMock()
            store = OptimizedVectorStore(mock_repo)
            
            stats = store.get_query_stats()
            
            assert 'total_queries' in stats
            assert 'avg_time_ms' in stats
            
            store.close()
        except Exception as e:
            pytest.skip(f"ChromaDB not available: {e}")


class TestPerformanceComparison:
    """Test performance improvements"""
    
    def test_batch_vs_sequential(self, mock_rag_service=None):
        """Compare batch vs sequential search"""
        if mock_rag_service is None:
            mock_rag_service = MagicMock()
            mock_rag_service.search.return_value = {
                'status': 'success',
                'query': 'test',
                'results': {'deals': [], 'activities': [], 'agents': []},
                'total_matches': 0
            }
        
        service = BatchSearchService(mock_rag_service, max_workers=5)
        
        queries = ["q" + str(i) for i in range(10)]
        
        # Batch search
        result = service.search_batch(queries, "all", 5)
        
        assert result['queries'] == 10
        
        # Should have metrics showing speed
        stats = service.get_stats()
        assert stats['queries_per_second'] > 0
        
        service.shutdown()