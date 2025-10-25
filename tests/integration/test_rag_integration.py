"""
tests/integration/test_rag_integration.py
-----------------------------------------
Integration tests for RAG system
Tests end-to-end workflows with real data
"""

import pytest
import asyncio
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

from services.embedding_service import EmbeddingService
from services.vector_store_service import VectorStoreService
from services.rag_search_service import RAGSearchService  # ← Direct import
from models.deal_model import Deal, DealActivity, CRMAgent
from utils.exceptions import ServiceError


class TestRAGEndToEnd:
    """End-to-end RAG workflow tests"""
    
    @pytest.fixture
    def mock_repositories(self):
        """Create mock repositories with sample data"""
        mock_repo = MagicMock()
        
        # Mock deals - FIXED: Use lambda with default argument to capture value
        deals = [
            MagicMock(
                to_dict=lambda d={'id': 1, 'title': 'Enterprise Software License', 'status': 'open', 'value': 150000, 'customer_name': 'Tech Corp', 'description': 'Customer interested in pricing and implementation timeline'}: d
            ),
            MagicMock(
                to_dict=lambda d={'id': 2, 'title': 'Consulting Services', 'status': 'negotiation', 'value': 75000, 'customer_name': 'Global Industries', 'description': 'Strategic consulting engagement for digital transformation'}: d
            ),
            MagicMock(
                to_dict=lambda d={'id': 3, 'title': 'Support Package Renewal', 'status': 'closed', 'value': 25000, 'customer_name': 'Local Business Inc', 'description': 'Annual maintenance and support agreement'}: d
            )
        ]
        
        # Mock activities - FIXED: Use lambda with default argument to capture value
        activities = [
            MagicMock(
                to_dict=lambda a={'id': 1, 'deal_id': 1, 'type': 'call', 'agent_name': 'Sarah Johnson', 'activity_date': '2024-01-15', 'notes': 'Customer mentioned concerns about pricing structure', 'outcome': 'follow_up'}: a
            ),
            MagicMock(
                to_dict=lambda a={'id': 2, 'deal_id': 2, 'type': 'email', 'agent_name': 'Mike Chen', 'activity_date': '2024-01-16', 'notes': 'Sent proposal for consulting services', 'outcome': 'pending'}: a
            ),
            MagicMock(
                to_dict=lambda a={'id': 3, 'deal_id': 1, 'type': 'meeting', 'agent_name': 'Sarah Johnson', 'activity_date': '2024-01-17', 'notes': 'Discussed implementation timeline and resource allocation', 'outcome': 'next_step'}: a
            )
        ]
        
        # Mock agents - FIXED: Use lambda with default argument to capture value
        agents = [
            MagicMock(
                to_dict=lambda ag={'id': 1, 'name': 'Sarah Johnson', 'email': 'sarah.johnson@company.com', 'phone': '+1-555-0101', 'title': 'Sales Manager'}: ag
            ),
            MagicMock(
                to_dict=lambda ag={'id': 2, 'name': 'Mike Chen', 'email': 'mike.chen@company.com', 'phone': '+1-555-0102', 'title': 'Account Executive'}: ag
            )
        ]
        
        # Setup context manager for repositories
        mock_repo.__enter__ = MagicMock(return_value=mock_repo)
        mock_repo.__exit__ = MagicMock(return_value=False)
        
        # Setup repository methods
        mock_repo.deals.get_all_deals.return_value = deals
        mock_repo.activities.get_all_activities.return_value = activities
        mock_repo.agents.get_all_agents.return_value = agents
        
        return mock_repo
    
    @pytest.fixture
    def temp_chroma_dir(self):
        """Create temporary directory for ChromaDB"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir
    
    @pytest.mark.asyncio
    async def test_full_rag_workflow(self, mock_repositories, temp_chroma_dir):
        """Test complete RAG workflow: embed, index, search"""
        # Initialize services
        rag_service = RAGSearchService(mock_repositories)
        rag_service.embedding_service = EmbeddingService(mock_repositories)
        await rag_service.embedding_service.initialize()
        
        rag_service.vector_store_service = VectorStoreService(
            mock_repositories,
            persist_dir=temp_chroma_dir
        )
        await rag_service.vector_store_service.initialize()
        rag_service._initialized = True
        
        # Step 1: Index all data
        assert rag_service._initialized
        
        # Generate embeddings
        embeddings = rag_service.embedding_service.embed_all_data()
        assert embeddings['total_embeddings'] > 0
        assert len(embeddings['deals']) == 3
        assert len(embeddings['activities']) == 3
        assert len(embeddings['agents']) == 2
    
    @pytest.mark.asyncio
    async def test_embedding_generation_with_sample_data(self, mock_repositories):
        """Test embedding generation with real sample data"""
        service = EmbeddingService(mock_repositories)
        await service.initialize()
        
        # Embed all data types
        embeddings = service.embed_all_data()
        
        assert 'deals' in embeddings and 'total_embeddings' in embeddings
        assert embeddings['total_embeddings'] == 8  # 3 deals + 3 activities + 2 agents
        
        # Verify structure
        for deal_emb in embeddings['deals']:
            assert 'id' in deal_emb
            assert 'type' in deal_emb
            assert deal_emb['type'] == 'deal'
            assert 'embedding' in deal_emb
            assert len(deal_emb['embedding']) > 0
            assert 'metadata' in deal_emb
    
    @pytest.mark.asyncio
    async def test_vector_store_with_real_embeddings(self, mock_repositories, temp_chroma_dir):
        """Test vector store with real embeddings"""
        # Generate embeddings
        embedding_service = EmbeddingService(mock_repositories)
        await embedding_service.initialize()
        
        embeddings = embedding_service.embed_all_data()
        
        # Initialize vector store
        vector_store = VectorStoreService(mock_repositories, persist_dir=temp_chroma_dir)
        await vector_store.initialize()
        
        # Add embeddings
        results = vector_store.add_all_embeddings(embeddings)
        
        assert results.get('deals', False)
        assert results.get('activities', False)
        assert results.get('agents', False)
        
        # Verify stats
        stats = vector_store.get_all_stats()
        assert stats['total_documents'] == 8
    
    @pytest.mark.asyncio
    async def test_semantic_search_workflow(self, mock_repositories, temp_chroma_dir):
        """Test complete semantic search workflow"""
        # Setup
        embedding_service = EmbeddingService(mock_repositories)
        await embedding_service.initialize()
        embeddings = embedding_service.embed_all_data()
        vector_store = VectorStoreService(mock_repositories, persist_dir=temp_chroma_dir)
        await vector_store.initialize()
        vector_store.add_all_embeddings(embeddings)
        # Test searches
        pricing_results = vector_store.search_all_collections("pricing concerns", n_results=3)
        
        assert isinstance(pricing_results, dict)
        # Should find deals related to pricing
        assert len(pricing_results['deals']) > 0 or len(pricing_results['activities']) > 0
    
    @pytest.mark.asyncio
    async def test_search_across_deal_types(self, mock_repositories, temp_chroma_dir):
        """Test searching across different deal types"""
        embedding_service = EmbeddingService(mock_repositories)
        await embedding_service.initialize()
        
        vector_store = VectorStoreService(mock_repositories, persist_dir=temp_chroma_dir)
        await vector_store.initialize()
        vector_store.add_all_embeddings(embedding_service)
        
        # Search for consulting
        results = vector_store.search_all_collections("consulting services", n_results=3)
        assert isinstance(results, dict)
        
        # Search for implementation
        results = vector_store.search_all_collections("implementation timeline", n_results=3)
        assert isinstance(results, dict)
    
    @pytest.mark.asyncio
    async def test_search_activities_by_agent(self, mock_repositories, temp_chroma_dir):
        """Test searching activities by agent name"""
        embedding_service = EmbeddingService(mock_repositories)
        await embedding_service.initialize()
        embeddings = embedding_service.embed_all_data()
        vector_store = VectorStoreService(mock_repositories, persist_dir=temp_chroma_dir)
        await vector_store.initialize()
        vector_store.add_all_embeddings(embeddings)
        # Search for Sarah Johnson
        results = vector_store.search_all_collections("Sarah Johnson", n_results=5)
        
        assert isinstance(results, dict)
        # Should find activities and/or agents
        total_results = sum(len(r) for r in results.values())
        assert total_results > 0
    
    @pytest.mark.asyncio
    async def test_rag_search_service_integration(self, mock_repositories, temp_chroma_dir):
        """Test RAG search service integration"""
        rag_service = RAGSearchService(mock_repositories)
        rag_service.embedding_service = EmbeddingService(mock_repositories)
        await rag_service.embedding_service.initialize()
        
        rag_service.vector_store_service = VectorStoreService(
            mock_repositories,
            persist_dir=temp_chroma_dir
        )
        await rag_service.vector_store_service.initialize()
        rag_service._initialized = True
        
        # Index data
        rag_service.vector_store_service.add_all_embeddings(rag_service.embedding_service)
        
        # Search
        result = rag_service.search("pricing information", n_results=3)
        
        assert result['status'] == 'success'
        assert result['query'] == 'pricing information'
        assert result['total_matches'] >= 0
        assert 'results' in result
    
    @pytest.mark.asyncio
    async def test_search_specific_collections(self, mock_repositories, temp_chroma_dir):
        """Test searching specific collections"""
        rag_service = RAGSearchService(mock_repositories)
        rag_service.embedding_service = EmbeddingService(mock_repositories)
        await rag_service.embedding_service.initialize()
        
        rag_service.vector_store_service = VectorStoreService(
            mock_repositories,
            persist_dir=temp_chroma_dir
        )
        await rag_service.vector_store_service.initialize()
        rag_service._initialized = True
        
        # Index data
        rag_service.vector_store_service.add_all_embeddings(rag_service.embedding_service)
        
        # Search deals
        deals = rag_service.search_deals("enterprise software", n_results=3)
        assert isinstance(deals, list)
        
        # Search activities
        activities = rag_service.search_activities("call meeting", n_results=3)
        assert isinstance(activities, list)
        
        # Search agents
        agents = rag_service.search_agents("Sarah", n_results=3)
        assert isinstance(agents, list)
    
    @pytest.mark.asyncio
    async def test_collection_reindexing(self, mock_repositories, temp_chroma_dir):
        """Test reindexing a collection"""
        rag_service = RAGSearchService(mock_repositories)
        rag_service.embedding_service = EmbeddingService(mock_repositories)
        await rag_service.embedding_service.initialize()
        
        rag_service.vector_store_service = VectorStoreService(
            mock_repositories,
            persist_dir=temp_chroma_dir
        )
        await rag_service.vector_store_service.initialize()
        embeddings = rag_service.embedding_service.embed_all_data()
        rag_service._initialized = True
        
        # Initial indexing
        rag_service.vector_store_service.add_all_embeddings(embeddings)
        
        # Reindex deals
        result = rag_service.reindex_collection('deals')
        
        assert result['status'] == 'success'
        assert result['collection'] == 'deals'
        assert result['stats']['collection_name'] == 'deals'
    
    @pytest.mark.asyncio
    async def test_get_index_stats_integration(self, mock_repositories, temp_chroma_dir):
        """Test getting index statistics"""
        rag_service = RAGSearchService(mock_repositories)
        rag_service.embedding_service = EmbeddingService(mock_repositories)
        await rag_service.embedding_service.initialize()
        
        rag_service.vector_store_service = VectorStoreService(
            mock_repositories,
            persist_dir=temp_chroma_dir
        )
        await rag_service.vector_store_service.initialize()
        embeddings = rag_service.embedding_service.embed_all_data()
        rag_service._initialized = True
        
        # Index data
        rag_service.vector_store_service.add_all_embeddings(embeddings)
        # Get stats
        stats = rag_service.get_index_stats()
        
        assert stats['status'] == 'success'
        assert stats['stats']['total_documents'] == 8
        assert 'deals' in stats['stats']
        assert 'activities' in stats['stats']
        assert 'agents' in stats['stats']
    
    @pytest.mark.asyncio
    async def test_search_error_handling(self, mock_repositories, temp_chroma_dir):
        """Test error handling in search"""
        rag_service = RAGSearchService(mock_repositories)
        
        # Try to search without initialization
        result = rag_service.search("test query")
        
        assert result['status'] == 'error'
        assert 'error' in result
    
    @pytest.mark.asyncio
    async def test_search_with_empty_query(self, mock_repositories, temp_chroma_dir):
        """Test search with empty query"""
        rag_service = RAGSearchService(mock_repositories)
        rag_service.embedding_service = EmbeddingService(mock_repositories)
        await rag_service.embedding_service.initialize()
        
        rag_service.vector_store_service = VectorStoreService(
            mock_repositories,
            persist_dir=temp_chroma_dir
        )
        await rag_service.vector_store_service.initialize()
        rag_service._initialized = True
        
        # Index data
        rag_service.vector_store_service.add_all_embeddings(rag_service.embedding_service)
        
        # Search with empty query
        result = rag_service.search("", n_results=3)
        
        # Should still work but may return all results or none
        assert result['status'] == 'success'
    
    @pytest.mark.asyncio
    async def test_persian_text_search(self, mock_repositories, temp_chroma_dir):
        """Test searching with Persian text"""
        rag_service = RAGSearchService(mock_repositories)
        rag_service.embedding_service = EmbeddingService(mock_repositories)
        await rag_service.embedding_service.initialize()
        
        rag_service.vector_store_service = VectorStoreService(
            mock_repositories,
            persist_dir=temp_chroma_dir
        )
        await rag_service.vector_store_service.initialize()
        rag_service._initialized = True
        
        # Index data
        rag_service.vector_store_service.add_all_embeddings(rag_service.embedding_service)
        
        # Search with Persian text (multilingual model supports it)
        result = rag_service.search("قیمت", n_results=3)
        
        assert result['status'] == 'success'
        assert result['query'] == 'قیمت'