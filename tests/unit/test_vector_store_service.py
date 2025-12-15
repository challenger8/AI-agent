"""
tests/unit/test_vector_store_service.py
----------------------------------------
Unit tests for VectorStoreService
Tests ChromaDB integration, embeddings management, and search operations
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch, call
from datetime import datetime

from services.vector_store_service import VectorStoreService
from utils.exceptions import ServiceError


class TestVectorStoreServiceInitialization:
    """Test VectorStoreService initialization"""

    def test_init_with_default_persist_dir(self):
        """Test initialization with default persist directory from RAGSettings"""
        with patch('services.vector_store_service.RAGSettings') as mock_settings:
            mock_settings.CHROMA_DB_DIR = '/tmp/chroma'

            service = VectorStoreService()

            assert service.persist_dir == '/tmp/chroma'
            assert service.client is None
            assert service.collections == {}
            mock_settings.validate_paths.assert_called_once()

    def test_init_with_custom_persist_dir(self):
        """Test initialization with custom persist directory"""
        service = VectorStoreService(persist_dir='/custom/path')

        assert service.persist_dir == '/custom/path'
        assert service.client is None
        assert service.collections == {}

    @pytest.mark.asyncio
    async def test_initialize_success(self):
        """Test successful ChromaDB initialization"""
        service = VectorStoreService(persist_dir='/tmp/test')

        with patch.object(service, '_setup_chromadb', new_callable=AsyncMock) as mock_setup:
            await service.initialize()

            mock_setup.assert_called_once()

    @pytest.mark.asyncio
    async def test_initialize_failure_raises_error(self):
        """Test initialization failure raises ServiceError"""
        service = VectorStoreService(persist_dir='/tmp/test')

        with patch.object(service, '_setup_chromadb', new_callable=AsyncMock, side_effect=Exception("DB error")):
            with pytest.raises(Exception):  # Will raise because raise_on_error=True
                await service.initialize()


class TestCollectionManagement:
    """Test collection management operations"""

    @pytest.fixture
    def service(self):
        """Create service with mocked ChromaDB client"""
        service = VectorStoreService(persist_dir='/tmp/test')
        service.client = MagicMock()
        return service

    def test_initialize_collections_success(self, service):
        """Test successful collection initialization"""
        mock_collection = MagicMock()
        service.client.get_or_create_collection.return_value = mock_collection

        service._initialize_collections()

        assert len(service.collections) == 3
        assert 'deals' in service.collections
        assert 'activities' in service.collections
        assert 'agents' in service.collections

        # Verify each collection was created with correct metadata
        assert service.client.get_or_create_collection.call_count == 3
        service.client.get_or_create_collection.assert_any_call(
            name='deals',
            metadata={"hnsw:space": "cosine"}
        )

    def test_initialize_collections_failure(self, service):
        """Test collection initialization failure"""
        service.client.get_or_create_collection.side_effect = Exception("Collection error")

        with pytest.raises(Exception):
            service._initialize_collections()

    def test_delete_collection_success(self, service):
        """Test successful collection deletion and recreation"""
        mock_collection = MagicMock()
        service.collections['deals'] = mock_collection
        service.client.delete_collection = MagicMock()
        service.client.get_or_create_collection.return_value = mock_collection

        result = service.delete_collection('deals')

        assert result is True
        service.client.delete_collection.assert_called_once_with(name='deals')
        service.client.get_or_create_collection.assert_called_once()

    def test_delete_nonexistent_collection(self, service):
        """Test deleting non-existent collection"""
        result = service.delete_collection('nonexistent')

        assert result is False


class TestEmbeddingsOperations:
    """Test embeddings add operations"""

    @pytest.fixture
    def service(self):
        """Create service with mocked collections"""
        service = VectorStoreService(persist_dir='/tmp/test')
        service.client = MagicMock()
        mock_collection = MagicMock()
        service.collections = {
            'deals': mock_collection,
            'activities': mock_collection,
            'agents': mock_collection
        }
        return service

    def test_add_embeddings_success(self, service):
        """Test successfully adding embeddings to collection"""
        embeddings_data = [
            {
                'id': 'deal_1',
                'embedding': [0.1, 0.2, 0.3],
                'text': 'Test deal',
                'metadata': {'type': 'deal', 'status': 'open'}
            },
            {
                'id': 'deal_2',
                'embedding': [0.4, 0.5, 0.6],
                'text': 'Another deal',
                'metadata': {'type': 'deal', 'status': 'won'}
            }
        ]

        result = service.add_embeddings(embeddings_data, 'deals')

        assert result is True
        assert service.collections['deals'].add.call_count == 2

    def test_add_embeddings_with_empty_metadata(self, service):
        """Test adding embeddings with empty metadata (should add default type)"""
        embeddings_data = [
            {
                'id': 'deal_1',
                'embedding': [0.1, 0.2, 0.3],
                'text': 'Test deal',
                'metadata': {}
            }
        ]

        result = service.add_embeddings(embeddings_data, 'deals')

        assert result is True
        # Verify metadata was added
        call_args = service.collections['deals'].add.call_args
        assert call_args[1]['metadatas'][0] == {'type': 'deals'}

    def test_add_embeddings_to_nonexistent_collection(self, service):
        """Test adding embeddings to non-existent collection"""
        embeddings_data = [{'id': '1', 'embedding': [0.1], 'text': 'test'}]

        result = service.add_embeddings(embeddings_data, 'nonexistent')

        assert result is False

    def test_add_embeddings_raises_on_error(self, service):
        """Test that add_embeddings raises ServiceError on failure"""
        service.collections['deals'].add.side_effect = Exception("DB error")
        embeddings_data = [{'id': '1', 'embedding': [0.1], 'text': 'test', 'metadata': {}}]

        with pytest.raises(ServiceError):
            service.add_embeddings(embeddings_data, 'deals')

    def test_add_all_embeddings_from_dict(self, service):
        """Test adding all embeddings from dictionary"""
        embeddings_dict = {
            'deals': [{'id': 'd1', 'embedding': [0.1], 'text': 'deal', 'metadata': {}}],
            'activities': [{'id': 'a1', 'embedding': [0.2], 'text': 'activity', 'metadata': {}}],
            'agents': [{'id': 'ag1', 'embedding': [0.3], 'text': 'agent', 'metadata': {}}]
        }

        with patch.object(service, 'add_embeddings', return_value=True) as mock_add:
            results = service.add_all_embeddings(embeddings_dict)

            assert results['deals'] is True
            assert results['activities'] is True
            assert results['agents'] is True
            assert mock_add.call_count == 3

    def test_add_all_embeddings_from_service(self, service):
        """Test adding all embeddings from EmbeddingService"""
        mock_embedding_service = MagicMock()
        mock_embedding_service.embed_all_data.return_value = {
            'deals': [{'id': 'd1', 'embedding': [0.1], 'text': 'deal', 'metadata': {}}]
        }

        with patch.object(service, 'add_embeddings', return_value=True) as mock_add:
            results = service.add_all_embeddings(mock_embedding_service)

            mock_embedding_service.embed_all_data.assert_called_once()
            assert results['deals'] is True


class TestSearchOperations:
    """Test search operations"""

    @pytest.fixture
    def service(self):
        """Create service with mocked collections"""
        service = VectorStoreService(persist_dir='/tmp/test')
        mock_collection = MagicMock()
        service.collections = {
            'deals': mock_collection,
            'activities': mock_collection,
            'agents': mock_collection
        }
        return service

    def test_search_success(self, service):
        """Test successful search operation"""
        mock_results = {
            'ids': [['deal_1', 'deal_2']],
            'distances': [[0.1, 0.2]],
            'documents': [['Deal 1', 'Deal 2']],
            'metadatas': [[{'status': 'open'}, {'status': 'won'}]]
        }
        service.collections['deals'].query.return_value = mock_results

        with patch('services.vector_store_service.SearchResultFormatter.format_chromadb_results') as mock_format:
            mock_format.return_value = [{'id': 'deal_1'}, {'id': 'deal_2'}]

            results = service.search('test query', 'deals', n_results=5)

            assert len(results) == 2
            service.collections['deals'].query.assert_called_once_with(
                query_texts=['test query'],
                n_results=5,
                where=None
            )
            mock_format.assert_called_once_with(mock_results)

    def test_search_with_metadata_filter(self, service):
        """Test search with metadata filter"""
        where_filter = {'status': 'open'}
        service.collections['deals'].query.return_value = {
            'ids': [[]], 'distances': [[]], 'documents': [[]], 'metadatas': [[]]
        }

        with patch('services.vector_store_service.SearchResultFormatter.format_chromadb_results', return_value=[]):
            service.search('test', 'deals', where=where_filter)

            service.collections['deals'].query.assert_called_once_with(
                query_texts=['test'],
                n_results=5,
                where=where_filter
            )

    def test_search_nonexistent_collection(self, service):
        """Test searching non-existent collection returns empty list"""
        results = service.search('test', 'nonexistent')

        assert results == []

    def test_search_with_error_returns_empty_list(self, service):
        """Test search error returns empty list"""
        service.collections['deals'].query.side_effect = Exception("Query error")

        results = service.search('test', 'deals')

        assert results == []

    def test_search_all_collections(self, service):
        """Test searching across all collections"""
        with patch.object(service, 'search') as mock_search:
            mock_search.side_effect = [
                [{'id': 'd1'}],  # deals
                [{'id': 'a1'}],  # activities
                [{'id': 'ag1'}]  # agents
            ]

            results = service.search_all_collections('test query', n_results=5)

            assert 'deals' in results
            assert 'activities' in results
            assert 'agents' in results
            assert len(results['deals']) == 1
            assert mock_search.call_count == 3

    def test_search_all_collections_with_error(self, service):
        """Test search_all_collections handles errors gracefully"""
        with patch.object(service, 'search', side_effect=Exception("Error")):
            results = service.search_all_collections('test query')

            assert results == {'deals': [], 'activities': [], 'agents': []}


class TestStatisticsOperations:
    """Test statistics operations"""

    @pytest.fixture
    def service(self):
        """Create service with mocked collections"""
        service = VectorStoreService(persist_dir='/tmp/test')
        mock_collection = MagicMock()
        mock_collection.count.return_value = 42
        service.collections = {
            'deals': mock_collection,
            'activities': mock_collection,
            'agents': mock_collection
        }
        return service

    def test_get_collection_stats(self, service):
        """Test getting collection statistics"""
        stats = service.get_collection_stats('deals')

        assert stats['collection_name'] == 'deals'
        assert stats['document_count'] == 42
        assert 'timestamp' in stats
        service.collections['deals'].count.assert_called_once()

    def test_get_collection_stats_nonexistent(self, service):
        """Test getting stats for non-existent collection returns empty dict"""
        stats = service.get_collection_stats('nonexistent')

        assert stats == {}

    def test_get_collection_stats_with_error(self, service):
        """Test get_collection_stats handles errors"""
        service.collections['deals'].count.side_effect = Exception("Count error")

        stats = service.get_collection_stats('deals')

        assert stats == {}

    def test_get_all_stats(self, service):
        """Test getting statistics for all collections"""
        stats = service.get_all_stats()

        assert 'deals' in stats
        assert 'activities' in stats
        assert 'agents' in stats
        assert stats['total_documents'] == 126  # 42 * 3
        assert 'timestamp' in stats

    def test_get_all_stats_with_error(self, service):
        """Test get_all_stats handles errors gracefully"""
        service.collections['deals'].count.side_effect = Exception("Error")

        stats = service.get_all_stats()

        assert stats == {}
