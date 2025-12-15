"""
tests/unit/test_chromadb_optimization.py
-----------------------------------------
Unit tests for ChromaDB query optimization components
Tests connection pooling, query optimization, and HNSW indexing
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch, call
from datetime import datetime

from services.chromadb_query_optimization import (
    ChromaDBConnectionPool,
    OptimizedVectorStoreQuery,
    OptimizedVectorStore
)
from utils.exceptions import ServiceError


class TestChromaDBConnectionPool:
    """Test ChromaDB connection pooling"""

    @patch('services.chromadb_query_optimization.chromadb.PersistentClient')
    def test_init_creates_connections(self, mock_client):
        """Test connection pool initialization creates connections"""
        with patch('services.chromadb_query_optimization.RAGSettings') as mock_settings:
            mock_settings.CHROMA_DB_DIR = '/tmp/chroma'

            pool = ChromaDBConnectionPool(max_connections=3)

            assert len(pool.pool) == 3
            assert len(pool.available) == 3
            assert all(pool.available)
            assert mock_client.call_count == 3

    @patch('services.chromadb_query_optimization.chromadb.PersistentClient')
    def test_get_connection_returns_available(self, mock_client):
        """Test getting connection from pool returns first available"""
        with patch('services.chromadb_query_optimization.RAGSettings') as mock_settings:
            mock_settings.CHROMA_DB_DIR = '/tmp/chroma'

            pool = ChromaDBConnectionPool(max_connections=2)

            connection = pool.get_connection()

            assert connection is not None
            assert pool.available[0] is False
            assert pool.available[1] is True

    @patch('services.chromadb_query_optimization.chromadb.PersistentClient')
    def test_return_connection_marks_available(self, mock_client):
        """Test returning connection marks it as available"""
        with patch('services.chromadb_query_optimization.RAGSettings') as mock_settings:
            mock_settings.CHROMA_DB_DIR = '/tmp/chroma'

            pool = ChromaDBConnectionPool(max_connections=2)

            connection = pool.get_connection()
            assert pool.available[0] is False

            pool.return_connection(connection)
            assert pool.available[0] is True

    @patch('services.chromadb_query_optimization.chromadb.PersistentClient')
    def test_close_all_clears_pool(self, mock_client):
        """Test closing all connections clears pool"""
        with patch('services.chromadb_query_optimization.RAGSettings') as mock_settings:
            mock_settings.CHROMA_DB_DIR = '/tmp/chroma'

            pool = ChromaDBConnectionPool(max_connections=2)

            pool.close_all()

            assert len(pool.pool) == 0
            assert len(pool.available) == 0

    @patch('services.chromadb_query_optimization.chromadb.PersistentClient')
    def test_get_connection_waits_when_all_busy(self, mock_client):
        """Test getting connection waits when all connections busy"""
        with patch('services.chromadb_query_optimization.RAGSettings') as mock_settings:
            mock_settings.CHROMA_DB_DIR = '/tmp/chroma'

            pool = ChromaDBConnectionPool(max_connections=1)

            # Get the only connection
            conn1 = pool.get_connection()
            assert pool.available[0] is False

            # Mock time.sleep to avoid actual wait
            with patch('services.chromadb_query_optimization.time.sleep'):
                # Set up pool to become available after recursive call
                pool.available[0] = True

                # Get connection (should wait and retry)
                conn2 = pool.get_connection()
                assert conn2 is not None


class TestOptimizedVectorStoreQuery:
    """Test optimized query execution"""

    @pytest.fixture
    def mock_pool(self):
        """Create mock connection pool"""
        pool = MagicMock()
        mock_client = MagicMock()
        mock_collection = MagicMock()

        pool.get_connection.return_value = mock_client
        mock_client.get_collection.return_value = mock_collection

        return pool, mock_client, mock_collection

    def test_search_success(self, mock_pool):
        """Test successful search query"""
        pool, mock_client, mock_collection = mock_pool

        # Mock query results
        mock_results = {
            'ids': [['id1', 'id2']],
            'distances': [[0.1, 0.2]],
            'documents': [['doc1', 'doc2']],
            'metadatas': [[{'type': 'deal'}, {'type': 'deal'}]]
        }
        mock_collection.query.return_value = mock_results

        # Mock formatter
        with patch('services.chromadb_query_optimization.SearchResultFormatter.format_chromadb_results') as mock_format:
            mock_format.return_value = [{'id': 'id1'}, {'id': 'id2'}]

            optimizer = OptimizedVectorStoreQuery(pool)
            results = optimizer.search('deals', [0.1, 0.2, 0.3], n_results=5)

            assert len(results) == 2
            assert results[0]['id'] == 'id1'
            pool.get_connection.assert_called_once()
            pool.return_connection.assert_called_once_with(mock_client)

    def test_search_with_metadata_filter(self, mock_pool):
        """Test search with metadata filter"""
        pool, mock_client, mock_collection = mock_pool

        mock_collection.query.return_value = {
            'ids': [[]], 'distances': [[]], 'documents': [[]], 'metadatas': [[]]
        }

        with patch('services.chromadb_query_optimization.SearchResultFormatter.format_chromadb_results', return_value=[]):
            optimizer = OptimizedVectorStoreQuery(pool)
            where_filter = {'status': 'open'}

            optimizer.search('deals', [0.1, 0.2], n_results=3, where=where_filter)

            # Verify where filter passed to query
            mock_collection.query.assert_called_once()
            call_args = mock_collection.query.call_args
            assert call_args[1]['where'] == where_filter

    def test_search_returns_connection_on_error(self, mock_pool):
        """Test search returns connection even on error"""
        pool, mock_client, mock_collection = mock_pool

        # Make query raise exception
        mock_collection.query.side_effect = Exception("Query error")

        optimizer = OptimizedVectorStoreQuery(pool)
        results = optimizer.search('deals', [0.1, 0.2])

        # Should return empty list on error
        assert results == []
        # Connection should still be returned to pool
        pool.return_connection.assert_called_once_with(mock_client)

    def test_update_stats(self, mock_pool):
        """Test query statistics are updated"""
        pool, _, _ = mock_pool

        optimizer = OptimizedVectorStoreQuery(pool)

        optimizer._update_stats(0.123)
        optimizer._update_stats(0.456)

        assert optimizer.query_stats['total_queries'] == 2
        assert optimizer.query_stats['total_time'] == 0.579

    def test_get_stats(self, mock_pool):
        """Test getting query statistics"""
        pool, _, _ = mock_pool

        optimizer = OptimizedVectorStoreQuery(pool)

        optimizer._update_stats(0.1)
        optimizer._update_stats(0.2)

        stats = optimizer.get_stats()

        assert stats['total_queries'] == 2
        assert stats['avg_time_ms'] == 150.0  # (0.1 + 0.2) / 2 * 1000
        assert stats['total_time'] == 0.3
        assert stats['queries_per_second'] > 0

    def test_get_stats_zero_queries(self, mock_pool):
        """Test getting stats with zero queries"""
        pool, _, _ = mock_pool

        optimizer = OptimizedVectorStoreQuery(pool)
        stats = optimizer.get_stats()

        assert stats['total_queries'] == 0
        assert stats['avg_time_ms'] == 0
        assert stats['queries_per_second'] == 0


class TestOptimizedVectorStore:
    """Test optimized vector store"""

    @pytest.fixture
    def mock_dependencies(self):
        """Create mocked dependencies"""
        with patch('services.chromadb_query_optimization.ChromaDBConnectionPool') as mock_pool_class:
            mock_pool = MagicMock()
            mock_client = MagicMock()
            mock_collection = MagicMock()

            mock_pool_class.return_value = mock_pool
            mock_pool.get_connection.return_value = mock_client
            mock_client.get_or_create_collection.return_value = mock_collection

            yield mock_pool_class, mock_pool, mock_client, mock_collection

    def test_init_creates_pool_and_optimizer(self, mock_dependencies):
        """Test initialization creates connection pool and optimizer"""
        mock_pool_class, mock_pool, _, _ = mock_dependencies

        store = OptimizedVectorStore()

        mock_pool_class.assert_called_once_with(max_connections=5)
        assert store.connection_pool is mock_pool
        assert store.query_optimizer is not None
        assert store.collections == {}

    @pytest.mark.asyncio
    async def test_initialize_success(self, mock_dependencies):
        """Test successful initialization"""
        mock_pool_class, mock_pool, mock_client, mock_collection = mock_dependencies

        store = OptimizedVectorStore()
        result = await store.initialize()

        assert result is True
        assert len(store.collections) == 3
        assert 'deals' in store.collections
        assert 'activities' in store.collections
        assert 'agents' in store.collections

        mock_pool.get_connection.assert_called_once()
        mock_pool.return_connection.assert_called_once_with(mock_client)

        # Verify HNSW metadata was set
        assert mock_client.get_or_create_collection.call_count == 3
        for call_obj in mock_client.get_or_create_collection.call_args_list:
            metadata = call_obj[1]['metadata']
            assert 'hnsw:space' in metadata
            assert metadata['hnsw:space'] == 'cosine'
            assert 'hnsw:construction_ef' in metadata
            assert 'hnsw:search_ef' in metadata

    @pytest.mark.asyncio
    async def test_initialize_failure_raises_error(self, mock_dependencies):
        """Test initialization failure raises ServiceError"""
        mock_pool_class, mock_pool, mock_client, _ = mock_dependencies

        # Make initialization fail
        mock_client.get_or_create_collection.side_effect = Exception("DB error")

        store = OptimizedVectorStore()

        with pytest.raises(ServiceError):
            await store.initialize()

    @pytest.mark.asyncio
    async def test_initialize_returns_connection_on_error(self, mock_dependencies):
        """Test initialize returns connection even on error"""
        mock_pool_class, mock_pool, mock_client, _ = mock_dependencies

        mock_client.get_or_create_collection.side_effect = Exception("DB error")

        store = OptimizedVectorStore()

        try:
            await store.initialize()
        except ServiceError:
            pass

        # Connection should be returned to pool
        mock_pool.return_connection.assert_called_once_with(mock_client)

    def test_search_delegates_to_optimizer(self, mock_dependencies):
        """Test search delegates to query optimizer"""
        mock_pool_class, mock_pool, _, _ = mock_dependencies

        store = OptimizedVectorStore()
        store.collections['deals'] = MagicMock()

        mock_results = [{'id': 'result1'}]
        store.query_optimizer.search = MagicMock(return_value=mock_results)

        results = store.search([0.1, 0.2], 'deals', n_results=5)

        assert results == mock_results
        store.query_optimizer.search.assert_called_once_with(
            'deals', [0.1, 0.2], 5, None
        )

    def test_search_nonexistent_collection(self, mock_dependencies):
        """Test searching non-existent collection returns empty list"""
        mock_pool_class, _, _, _ = mock_dependencies

        store = OptimizedVectorStore()
        results = store.search([0.1, 0.2], 'nonexistent')

        assert results == []

    def test_add_embeddings_batch_success(self, mock_dependencies):
        """Test successful batch embedding addition"""
        mock_pool_class, mock_pool, mock_client, _ = mock_dependencies

        mock_collection = MagicMock()
        mock_client.get_collection.return_value = mock_collection

        store = OptimizedVectorStore()
        store.collections['deals'] = MagicMock()

        embeddings_data = [
            {
                'id': 'deal1',
                'embedding': [0.1, 0.2],
                'text': 'Deal text',
                'metadata': {'status': 'open'}
            },
            {
                'id': 'deal2',
                'embedding': [0.3, 0.4],
                'text': 'Another deal',
                'metadata': {}
            }
        ]

        result = store.add_embeddings_batch(embeddings_data, 'deals')

        assert result is True
        mock_collection.add.assert_called_once()

        # Verify empty metadata was filled with default type
        call_args = mock_collection.add.call_args
        metadatas = call_args[1]['metadatas']
        assert metadatas[1]['type'] == 'deals'

    def test_add_embeddings_batch_nonexistent_collection(self, mock_dependencies):
        """Test adding to non-existent collection returns False"""
        mock_pool_class, _, _, _ = mock_dependencies

        store = OptimizedVectorStore()

        embeddings_data = [{'id': '1', 'embedding': [0.1], 'text': 'test'}]
        result = store.add_embeddings_batch(embeddings_data, 'nonexistent')

        assert result is False

    def test_add_embeddings_batch_returns_connection_on_error(self, mock_dependencies):
        """Test batch add returns connection even on error"""
        mock_pool_class, mock_pool, mock_client, _ = mock_dependencies

        mock_collection = MagicMock()
        mock_collection.add.side_effect = Exception("Add error")
        mock_client.get_collection.return_value = mock_collection

        store = OptimizedVectorStore()
        store.collections['deals'] = MagicMock()

        embeddings_data = [{'id': '1', 'embedding': [0.1], 'text': 'test', 'metadata': {}}]
        result = store.add_embeddings_batch(embeddings_data, 'deals')

        assert result is False
        mock_pool.return_connection.assert_called_once_with(mock_client)

    def test_get_query_stats(self, mock_dependencies):
        """Test getting query statistics"""
        mock_pool_class, _, _, _ = mock_dependencies

        store = OptimizedVectorStore()

        mock_stats = {'total_queries': 10, 'avg_time_ms': 50}
        store.query_optimizer.get_stats = MagicMock(return_value=mock_stats)

        stats = store.get_query_stats()

        assert stats == mock_stats

    def test_close(self, mock_dependencies):
        """Test closing vector store"""
        mock_pool_class, mock_pool, _, _ = mock_dependencies

        store = OptimizedVectorStore()
        store.close()

        mock_pool.close_all.assert_called_once()
