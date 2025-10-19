"""
tests/unit/test_rag_service.py
------------------------------
Unit tests for RAG (Retrieval-Augmented Generation) system
Tests embedding generation, vector store, and search functionality
"""

import pytest
import asyncio
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from typing import List, Dict, Any

from services.embedding_service import EmbeddingService
from services.vector_store_service import VectorStoreService
from services.rag_search_service import RAGSearchService
from utils.exceptions import ServiceError


class TestEmbeddingService:
    """Test embedding service"""
    
    @pytest.fixture
    def mock_repositories(self):
        """Mock repositories"""
        mock_repo = MagicMock()
        mock_repo.deals.get_all_deals.return_value = []
        mock_repo.activities.get_all_activities.return_value = []
        mock_repo.agents.get_all_agents.return_value = []
        return mock_repo
    
    @pytest.fixture
    def embedding_service(self, mock_repositories):
        """Initialize embedding service"""
        service = EmbeddingService(mock_repositories)
        return service
    
    @pytest.mark.asyncio
    async def test_initialize_embedding_service(self, embedding_service):
        """Test embedding service initialization"""
        # Skip - requires real model loading
        pytest.skip("Requires real SentenceTransformer model - test in integration suite")
    
    def test_format_deal_text(self, embedding_service):
        """Test deal text formatting"""
        deal = {
            'id': 1,
            'title': 'Test Deal',
            'status': 'open',
            'value': 50000,
            'customer_name': 'Acme Corp',
            'description': 'Test description'
        }
        
        text = embedding_service._format_deal_text(deal)
        
        assert 'Test Deal' in text
        assert 'open' in text
        assert 'Acme Corp' in text
        assert '|' in text
    
    def test_format_activity_text(self, embedding_service):
        """Test activity text formatting"""
        activity = {
            'id': 1,
            'type': 'call',
            'agent_name': 'John Doe',
            'activity_date': '2024-01-15',
            'notes': 'Customer interested',
            'outcome': 'follow_up'
        }
        
        text = embedding_service._format_activity_text(activity)
        
        assert 'call' in text
        assert 'John Doe' in text
        assert 'follow_up' in text
        assert '|' in text
    
    def test_format_agent_text(self, embedding_service):
        """Test agent text formatting"""
        agent = {
            'id': 1,
            'name': 'Jane Smith',
            'email': 'jane@example.com',
            'phone': '+1234567890',
            'title': 'Sales Manager'
        }
        
        text = embedding_service._format_agent_text(agent)
        
        assert 'Jane Smith' in text
        assert 'jane@example.com' in text
        assert 'Sales Manager' in text
    
    @pytest.mark.asyncio
    async def test_embed_text(self, embedding_service):
        """Test text embedding"""
        # Mock the model
        mock_model = MagicMock()
        mock_model.encode.return_value = __import__('numpy').array([0.1] * 384)
        embedding_service.model = mock_model
        
        text = "This is a test for embedding"
        embedding = embedding_service.embed_text(text)
        
        assert embedding is not None
        assert isinstance(embedding, list)
        assert len(embedding) > 0
        assert all(isinstance(x, (float, int)) for x in embedding)
    
    @pytest.mark.asyncio
    async def test_embed_text_without_init(self, embedding_service):
        """Test embedding without initialization"""
        text = "Test text"
        embedding = embedding_service.embed_text(text)
        
        assert embedding is None
    
    @pytest.mark.asyncio
    async def test_embed_deals_empty(self, embedding_service, mock_repositories):
        """Test embedding empty deals"""
        await embedding_service.initialize()
        
        result = embedding_service.embed_deals()
        
        assert isinstance(result, list)
        assert len(result) == 0
    
    @pytest.mark.asyncio
    async def test_embed_activities_empty(self, embedding_service):
        """Test embedding empty activities"""
        await embedding_service.initialize()
        
        result = embedding_service.embed_activities()
        
        assert isinstance(result, list)
        assert len(result) == 0
    
    @pytest.mark.asyncio
    async def test_embed_agents_empty(self, embedding_service):
        """Test embedding empty agents"""
        await embedding_service.initialize()
        
        result = embedding_service.embed_agents()
        
        assert isinstance(result, list)
        assert len(result) == 0


class TestVectorStoreService:
    """Test vector store service"""
    
    @pytest.fixture
    def mock_repositories(self):
        """Mock repositories"""
        return MagicMock()
    
    @pytest.fixture
    def vector_store_service(self, mock_repositories, tmp_path):
        """Initialize vector store service"""
        persist_dir = str(tmp_path / "chroma_db")
        service = VectorStoreService(mock_repositories, persist_dir=persist_dir)
        return service
    
    @pytest.mark.asyncio
    async def test_initialize_vector_store(self, vector_store_service):
        """Test vector store initialization"""
        await vector_store_service.initialize()
        
        assert vector_store_service.client is not None
        assert 'deals' in vector_store_service.collections
        assert 'activities' in vector_store_service.collections
        assert 'agents' in vector_store_service.collections
    
    @pytest.mark.asyncio
    async def test_add_embeddings(self, vector_store_service):
        """Test adding embeddings to vector store"""
        await vector_store_service.initialize()
        
        embeddings_data = [
            {
                'id': '1',
                'text': 'Test deal one',
                'embedding': [0.1] * 384,
                'metadata': {'title': 'Deal 1', 'status': 'open', 'type': 'deal'}
            },
            {
                'id': '2',
                'text': 'Test deal two',
                'embedding': [0.2] * 384,
                'metadata': {'title': 'Deal 2', 'status': 'closed', 'type': 'deal'}
            }
        ]
        
        result = vector_store_service.add_embeddings(embeddings_data, 'deals')
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_add_embeddings_invalid_collection(self, vector_store_service):
        """Test adding embeddings to invalid collection"""
        await vector_store_service.initialize()
        
        embeddings_data = [
            {
                'id': '1',
                'text': 'Test',
                'embedding': [0.1] * 384,
                'metadata': {'type': 'test'}
            }
        ]
        
        result = vector_store_service.add_embeddings(embeddings_data, 'invalid_collection')
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_search_empty_collection(self, vector_store_service):
        """Test search in empty collection"""
        await vector_store_service.initialize()
        
        results = vector_store_service.search("test query", "deals", n_results=5)
        
        assert isinstance(results, list)
        assert len(results) == 0
    
    @pytest.mark.asyncio
    async def test_search_with_results(self, vector_store_service):
        """Test search with actual results"""
        await vector_store_service.initialize()
        
        # Add test embeddings
        embeddings_data = [
            {
                'id': '1',
                'text': 'Customer wants pricing information',
                'embedding': [0.1] * 384,
                'metadata': {'title': 'Pricing Deal', 'status': 'open', 'type': 'deal'}
            },
            {
                'id': '2',
                'text': 'Customer interested in features',
                'embedding': [0.2] * 384,
                'metadata': {'title': 'Feature Deal', 'status': 'open', 'type': 'deal'}
            }
        ]
        
        vector_store_service.add_embeddings(embeddings_data, 'deals')
        
        # Search
        results = vector_store_service.search("pricing information", "deals", n_results=5)
        
        assert isinstance(results, list)
        assert len(results) > 0
        assert 'id' in results[0]
        assert 'similarity' in results[0]
    
    @pytest.mark.asyncio
    async def test_search_all_collections(self, vector_store_service):
        """Test searching all collections"""
        await vector_store_service.initialize()
        
        results = vector_store_service.search_all_collections("test query", n_results=5)
        
        assert isinstance(results, dict)
        assert 'deals' in results
        assert 'activities' in results
        assert 'agents' in results
    
    @pytest.mark.asyncio
    async def test_delete_collection(self, vector_store_service):
        """Test collection deletion and recreation"""
        await vector_store_service.initialize()
        
        # Add data
        embeddings_data = [
            {
                'id': '1',
                'text': 'Test',
                'embedding': [0.1] * 384,
                'metadata': {'type': 'test'}
            }
        ]
        vector_store_service.add_embeddings(embeddings_data, 'deals')
        
        # Delete
        result = vector_store_service.delete_collection('deals')
        
        assert result is True
        assert 'deals' in vector_store_service.collections
    
    @pytest.mark.asyncio
    async def test_get_collection_stats(self, vector_store_service):
        """Test getting collection statistics"""
        await vector_store_service.initialize()
        
        stats = vector_store_service.get_collection_stats('deals')
        
        assert isinstance(stats, dict)
        assert 'collection_name' in stats
        assert 'document_count' in stats
        assert stats['collection_name'] == 'deals'
    
    @pytest.mark.asyncio
    async def test_get_all_stats(self, vector_store_service):
        """Test getting all collection stats"""
        await vector_store_service.initialize()
        
        stats = vector_store_service.get_all_stats()
        
        assert isinstance(stats, dict)
        assert 'deals' in stats
        assert 'activities' in stats
        assert 'agents' in stats
        assert 'total_documents' in stats


class TestRAGSearchService:
    """Test RAG search service"""
    
    @pytest.fixture
    def mock_repositories(self):
        """Mock repositories"""
        return MagicMock()
    
    @pytest.fixture
    def rag_search_service(self, mock_repositories):
        """Initialize RAG search service"""
        service = RAGSearchService(mock_repositories)
        service.embedding_service = MagicMock(spec=EmbeddingService)
        service.vector_store_service = MagicMock(spec=VectorStoreService)
        service._initialized = True
        return service
    
    @pytest.mark.asyncio
    async def test_rag_search_not_initialized(self, mock_repositories):
        """Test search without initialization"""
        service = RAGSearchService(mock_repositories)
        
        # Should return error dict, not raise exception
        result = service.search("test query")
        assert result['status'] == 'error'
    
    @pytest.mark.asyncio
    async def test_search_all_collections(self, rag_search_service):
        """Test searching all collections"""
        rag_search_service.vector_store_service.search_all_collections.return_value = {
            'deals': [
                {
                    'id': '1',
                    'text': 'Test deal',
                    'metadata': {'title': 'Deal 1'},
                    'similarity': 0.95,
                    'distance': 0.05
                }
            ],
            'activities': [],
            'agents': []
        }
        
        result = rag_search_service.search("test query", n_results=5)
        
        assert result['status'] == 'success'
        assert result['query'] == 'test query'
        assert result['total_matches'] == 1
        assert 'deals' in result['results']
    
    @pytest.mark.asyncio
    async def test_search_deals_only(self, rag_search_service):
        """Test searching deals only"""
        rag_search_service.vector_store_service.search.return_value = [
            {
                'id': '1',
                'text': 'Test deal',
                'metadata': {'title': 'Deal 1'},
                'similarity': 0.95,
                'distance': 0.05
            }
        ]
        
        result = rag_search_service.search_deals("test query", n_results=5)
        
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]['type'] == 'deal'
    
    @pytest.mark.asyncio
    async def test_search_activities_only(self, rag_search_service):
        """Test searching activities only"""
        rag_search_service.vector_store_service.search.return_value = [
            {
                'id': '1',
                'text': 'Test activity',
                'metadata': {'type': 'call'},
                'similarity': 0.92,
                'distance': 0.08
            }
        ]
        
        result = rag_search_service.search_activities("test query", n_results=5)
        
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]['type'] == 'activity'
    
    @pytest.mark.asyncio
    async def test_search_agents_only(self, rag_search_service):
        """Test searching agents only"""
        rag_search_service.vector_store_service.search.return_value = [
            {
                'id': '1',
                'text': 'Test agent',
                'metadata': {'name': 'John Doe'},
                'similarity': 0.88,
                'distance': 0.12
            }
        ]
        
        result = rag_search_service.search_agents("test query", n_results=5)
        
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]['type'] == 'agent'
    
    @pytest.mark.asyncio
    async def test_search_with_filters(self, rag_search_service):
        """Test search with metadata filters"""
        rag_search_service.vector_store_service.search.return_value = [
            {
                'id': '1',
                'text': 'Test deal',
                'metadata': {'status': 'open'},
                'similarity': 0.95,
                'distance': 0.05
            }
        ]
        
        filters = {'status': 'open'}
        result = rag_search_service.search_with_filters("test query", filters=filters)
        
        assert result['status'] == 'success'
        assert result['filters'] == filters
    
    @pytest.mark.asyncio
    async def test_get_index_stats(self, rag_search_service):
        """Test getting index statistics"""
        rag_search_service.vector_store_service.get_all_stats.return_value = {
            'deals': {'collection_name': 'deals', 'document_count': 10},
            'activities': {'collection_name': 'activities', 'document_count': 50},
            'agents': {'collection_name': 'agents', 'document_count': 5},
            'total_documents': 65
        }
        
        result = rag_search_service.get_index_stats()
        
        assert result['status'] == 'success'
        assert result['stats']['total_documents'] == 65
    
    @pytest.mark.asyncio
    async def test_reindex_invalid_collection(self, rag_search_service):
        """Test reindexing invalid collection"""
        with pytest.raises(ServiceError):
            await rag_search_service.reindex_collection('invalid_type')
    
    @pytest.mark.asyncio
    async def test_format_search_results(self, rag_search_service):
        """Test formatting search results"""
        raw_results = {
            'deals': [
                {
                    'id': '1',
                    'text': 'Test deal',
                    'metadata': {'title': 'Deal 1'},
                    'similarity': 0.95,
                    'distance': 0.05
                }
            ],
            'activities': [],
            'agents': []
        }
        
        formatted = rag_search_service._format_search_results(raw_results)
        
        assert 'deals' in formatted
        assert 'activities' in formatted
        assert 'agents' in formatted
        assert len(formatted['deals']) == 1
        assert formatted['deals'][0]['type'] == 'deal'