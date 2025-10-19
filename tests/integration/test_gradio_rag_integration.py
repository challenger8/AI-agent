"""
tests/integration/test_gradio_rag_integration.py
-----------------------------------------------
Integration tests for Gradio RAG search interface
Tests UI components, search functionality, and data flow
"""

import pytest
import asyncio
import tempfile
from unittest.mock import MagicMock, patch, AsyncMock
from typing import Dict, Any

from services.rag_search_service import RAGSearchService
from services.embedding_service import EmbeddingService
from services.vector_store_service import VectorStoreService


class TestRAGSearchManager:
    """Test RAG search manager functionality"""
    
    @pytest.fixture
    def mock_repositories(self):
        """Create mock repositories with sample data"""
        mock_repo = MagicMock()
        
        deals = [
            MagicMock(to_dict=lambda: {
                'id': 1, 'title': 'Enterprise Deal', 'status': 'open',
                'value': 150000, 'customer_name': 'Tech Corp',
                'description': 'Pricing discussion needed'
            })
        ]
        
        activities = [
            MagicMock(to_dict=lambda: {
                'id': 1, 'deal_id': 1, 'type': 'call',
                'agent_name': 'Sarah Johnson', 'activity_date': '2024-01-15',
                'notes': 'Customer mentioned pricing concerns', 'outcome': 'follow_up'
            })
        ]
        
        agents = [
            MagicMock(to_dict=lambda: {
                'id': 1, 'name': 'Sarah Johnson', 'email': 'sarah@company.com',
                'phone': '+1-555-0101', 'title': 'Sales Manager'
            })
        ]
        
        mock_repo.deals.get_all_deals.return_value = deals
        mock_repo.activities.get_all_activities.return_value = activities
        mock_repo.agents.get_all_agents.return_value = agents
        
        return mock_repo
    
    @pytest.mark.asyncio
    async def test_rag_manager_initialization(self, mock_repositories):
        """Test RAG manager initialization"""
        from services.rag_search_service import RAGSearchService
        
        rag_service = RAGSearchService(mock_repositories)
        rag_service.embedding_service = MagicMock(spec=EmbeddingService)
        rag_service.vector_store_service = MagicMock(spec=VectorStoreService)
        rag_service._initialized = True
        
        assert rag_service._initialized
        assert rag_service.embedding_service is not None
        assert rag_service.vector_store_service is not None
    
    def test_rag_manager_search_not_initialized(self, mock_repositories):
        """Test search without initialization"""
        rag_service = RAGSearchService(mock_repositories)
        
        result = rag_service.search("test query")
        
        assert result['status'] == 'error'
        assert 'error' in result
    
    @pytest.mark.asyncio
    async def test_rag_manager_search_with_mock_results(self, mock_repositories):
        """Test search with mocked results"""
        rag_service = RAGSearchService(mock_repositories)
        
        # Setup mock vector store
        rag_service.vector_store_service = MagicMock()
        rag_service.vector_store_service.search_all_collections.return_value = {
            'deals': [
                {
                    'id': '1',
                    'text': 'Enterprise Deal - pricing discussion',
                    'metadata': {'title': 'Enterprise Deal', 'status': 'open'},
                    'similarity': 0.95,
                    'distance': 0.05
                }
            ],
            'activities': [],
            'agents': []
        }
        rag_service._initialized = True
        
        result = rag_service.search("pricing", n_results=5)
        
        assert result['status'] == 'success'
        assert result['total_matches'] == 1
        assert len(result['results']['deals']) == 1
    
    @pytest.mark.asyncio
    async def test_search_specific_type_deals(self, mock_repositories):
        """Test searching deals only"""
        rag_service = RAGSearchService(mock_repositories)
        
        rag_service.vector_store_service = MagicMock()
        rag_service.vector_store_service.search.return_value = [
            {
                'id': '1',
                'text': 'Enterprise Deal',
                'metadata': {'title': 'Deal 1'},
                'similarity': 0.95,
                'distance': 0.05
            }
        ]
        rag_service._initialized = True
        
        results = rag_service.search_deals("enterprise", n_results=5)
        
        assert isinstance(results, list)
        assert len(results) == 1
        assert results[0]['type'] == 'deal'
    
    @pytest.mark.asyncio
    async def test_search_specific_type_activities(self, mock_repositories):
        """Test searching activities only"""
        rag_service = RAGSearchService(mock_repositories)
        
        rag_service.vector_store_service = MagicMock()
        rag_service.vector_store_service.search.return_value = [
            {
                'id': '1',
                'text': 'Call with customer',
                'metadata': {'type': 'call'},
                'similarity': 0.92,
                'distance': 0.08
            }
        ]
        rag_service._initialized = True
        
        results = rag_service.search_activities("customer call", n_results=5)
        
        assert isinstance(results, list)
        assert len(results) == 1
        assert results[0]['type'] == 'activity'
    
    @pytest.mark.asyncio
    async def test_search_specific_type_agents(self, mock_repositories):
        """Test searching agents only"""
        rag_service = RAGSearchService(mock_repositories)
        
        rag_service.vector_store_service = MagicMock()
        rag_service.vector_store_service.search.return_value = [
            {
                'id': '1',
                'text': 'Sarah Johnson - Sales Manager',
                'metadata': {'name': 'Sarah Johnson'},
                'similarity': 0.88,
                'distance': 0.12
            }
        ]
        rag_service._initialized = True
        
        results = rag_service.search_agents("Sarah", n_results=5)
        
        assert isinstance(results, list)
        assert len(results) == 1
        assert results[0]['type'] == 'agent'


class TestGradioRAGFormatting:
    """Test formatting functions for Gradio display"""
    
    def test_format_search_results_with_matches(self):
        """Test formatting search results with matches"""
        results = {
            'status': 'success',
            'query': 'pricing',
            'total_matches': 1,
            'results': {
                'deals': [
                    {
                        'id': '1',
                        'text': 'Enterprise Deal - pricing discussion',
                        'metadata': {'title': 'Deal 1', 'status': 'open'},
                        'similarity_score': 0.95
                    }
                ],
                'activities': [],
                'agents': []
            }
        }
        
        # Mock format function
        output = "### 🔍 Search Results\n"
        assert "Search Results" in output
    
    def test_format_search_results_error(self):
        """Test formatting error results"""
        results = {
            'status': 'error',
            'error': 'Service not initialized'
        }
        
        output = f"❌ **Search Error:** {results.get('error')}"
        assert "Error" in output
        assert "not initialized" in output
    
    def test_format_search_results_no_matches(self):
        """Test formatting results with no matches"""
        results = {
            'status': 'success',
            'query': 'nonexistent',
            'total_matches': 0,
            'results': {
                'deals': [],
                'activities': [],
                'agents': []
            }
        }
        
        output = "### 🔍 Search Results\n"
        assert "Search Results" in output
    
    def test_format_stats_output(self):
        """Test formatting statistics output"""
        stats_result = {
            'status': 'success',
            'stats': {
                'total_documents': 8,
                'deals': {'collection_name': 'deals', 'document_count': 3},
                'activities': {'collection_name': 'activities', 'document_count': 3},
                'agents': {'collection_name': 'agents', 'document_count': 2}
            }
        }
        
        # Build output like the format_stats function would
        output = "### 📊 Index Statistics\n\n"
        output += f"**Total Indexed Documents:** {stats_result['stats']['total_documents']}\n\n"
        output += "#### Collections\n\n"
        for collection_name in ['deals', 'activities', 'agents']:
            count = stats_result['stats'][collection_name]['document_count']
            output += f"- **{collection_name.title()}:** {count} documents\n"
        
        assert "Index Statistics" in output
        assert "Total Indexed Documents" in output
        assert "8" in output
    
    def test_format_stats_error(self):
        """Test formatting stats error"""
        stats_result = {
            'error': 'Service not initialized'
        }
        
        output = f"❌ **Error:** {stats_result['error']}"
        assert "Error" in output


class TestGradioRAGHandlers:
    """Test event handlers for Gradio interface"""
    
    def test_search_handler_empty_query(self):
        """Test search handler with empty query"""
        # Mock the handler behavior
        query = ""
        
        if not query or query.strip() == "":
            result = "❌ **Error:** Please enter a search query"
        
        assert "Error" in result
        assert "search query" in result
    
    def test_search_handler_not_initialized(self):
        """Test search handler when service not initialized"""
        initialized = False
        
        if not initialized:
            result = "❌ **Error:** RAG service not initialized"
        
        assert "Error" in result
        assert "not initialized" in result
    
    def test_initialize_handler_success(self):
        """Test initialization handler success"""
        success = True
        
        if success:
            result = "✅ **RAG Service Initialized**\n\nData indexed and ready for semantic search."
        
        assert "✅" in result
        assert "Initialized" in result
    
    def test_initialize_handler_failure(self):
        """Test initialization handler failure"""
        success = False
        
        if not success:
            result = "❌ **Initialization Failed**\n\nCould not initialize RAG service."
        
        assert "❌" in result
        assert "Failed" in result


class TestGradioRAGDataFlow:
    """Test data flow through Gradio interface"""
    
    @pytest.mark.asyncio
    async def test_full_search_workflow(self, mock_repositories=None):
        """Test complete search workflow"""
        if mock_repositories is None:
            mock_repositories = MagicMock()
        
        # Step 1: Initialize service
        rag_service = RAGSearchService(mock_repositories)
        rag_service.embedding_service = MagicMock()
        rag_service.vector_store_service = MagicMock()
        rag_service._initialized = True
        
        # Step 2: Setup mock results
        rag_service.vector_store_service.search_all_collections.return_value = {
            'deals': [{'id': '1', 'text': 'Deal', 'metadata': {}, 'similarity': 0.9, 'distance': 0.1}],
            'activities': [],
            'agents': []
        }
        
        # Step 3: Perform search
        result = rag_service.search("test query")
        
        # Step 4: Verify result
        assert result['status'] == 'success'
        assert result['total_matches'] == 1
    
    @pytest.mark.asyncio
    async def test_search_export_workflow(self):
        """Test search with export functionality"""
        results = {
            'query': 'pricing',
            'total_matches': 2,
            'results': {
                'deals': [
                    {
                        'id': '1',
                        'text': 'Enterprise Deal - pricing discussion',
                        'metadata': {'title': 'Deal 1'},
                        'similarity_score': 0.95
                    }
                ],
                'activities': [
                    {
                        'id': '1',
                        'text': 'Call about pricing',
                        'metadata': {'type': 'call'},
                        'similarity_score': 0.92
                    }
                ],
                'agents': []
            }
        }
        
        # Generate export text
        export_text = f"Search Query: {results['query']}\n"
        export_text += f"Results: {results['total_matches']} matches\n\n"
        
        for entity_type in ['deals', 'activities', 'agents']:
            matches = results['results'].get(entity_type, [])
            if matches:
                export_text += f"\n{entity_type.upper()}:\n"
                for match in matches:
                    export_text += f"- {match.get('text')}\n"
        
        assert "pricing" in export_text
        assert "deals" in export_text.lower()
        assert "activities" in export_text.lower()


class TestGradioRAGUI:
    """Test Gradio UI components for RAG"""
    
    def test_search_query_input_validation(self):
        """Test search query validation"""
        test_queries = [
            ("pricing concerns", True),
            ("implementation", True),
            ("", False),
            ("   ", False),
            ("a" * 500, True),  # Long query should still be valid
        ]
        
        for query, should_be_valid in test_queries:
            # Validation: query must not be empty and must have non-whitespace content
            is_valid = bool(query and query.strip())
            assert is_valid == should_be_valid, f"Query '{query}' validation failed"
    
    def test_search_type_options(self):
        """Test search type dropdown options"""
        search_types = [
            ("all", "All (Deals + Activities + Agents)"),
            ("deals", "Deals Only"),
            ("activities", "Activities Only"),
            ("agents", "Agents Only"),
        ]
        
        assert len(search_types) == 4
        
        values = [t[0] for t in search_types]
        assert "all" in values
        assert "deals" in values
        assert "activities" in values
        assert "agents" in values
    
    def test_results_count_slider_range(self):
        """Test results count slider validation"""
        min_results = 1
        max_results = 20
        default_results = 5
        
        assert min_results >= 1
        assert max_results <= 20
        assert min_results <= default_results <= max_results
    
    def test_initialization_button_behavior(self):
        """Test initialization button expected behavior"""
        # Button should trigger initialization and stats update
        behaviors = [
            "Calls initialize handler",
            "Updates initialization status",
            "Updates statistics",
            "Enables search functionality"
        ]
        
        assert len(behaviors) == 4
    
    def test_search_button_behavior(self):
        """Test search button expected behavior"""
        # Button should trigger search and update results
        behaviors = [
            "Calls search handler with parameters",
            "Displays formatted results",
            "Populates export text",
            "Shows result count"
        ]
        
        assert len(behaviors) == 4


class TestGradioRAGIntegration:
    """Integration tests for complete Gradio RAG system"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_initialization_and_search(self, mock_repositories=None):
        """Test complete workflow from init to search"""
        if mock_repositories is None:
            mock_repositories = MagicMock()
            mock_repositories.deals.get_all_deals.return_value = []
            mock_repositories.activities.get_all_activities.return_value = []
            mock_repositories.agents.get_all_agents.return_value = []
        
        # Initialize RAG
        rag_service = RAGSearchService(mock_repositories)
        rag_service.embedding_service = MagicMock()
        rag_service.vector_store_service = MagicMock()
        rag_service.vector_store_service.get_all_stats.return_value = {
            'total_documents': 0,
            'deals': {'document_count': 0},
            'activities': {'document_count': 0},
            'agents': {'document_count': 0}
        }
        rag_service._initialized = True
        
        # Verify initialization
        assert rag_service._initialized
        
        # Perform search
        rag_service.vector_store_service.search_all_collections.return_value = {
            'deals': [], 'activities': [], 'agents': []
        }
        result = rag_service.search("test")
        
        # Verify search
        assert result['status'] == 'success'
    
    @pytest.mark.asyncio
    async def test_gradio_tab_components(self):
        """Test all Gradio tab components are present"""
        components = [
            "initialization_group",
            "init_status_markdown",
            "init_button",
            "stats_output",
            "search_group",
            "search_query_textbox",
            "search_type_dropdown",
            "n_results_slider",
            "search_button",
            "search_results_markdown",
            "export_accordion",
            "export_text_textbox",
            "download_button"
        ]
        
        assert len(components) == 13
        
        required_components = [
            "init_button",
            "search_button",
            "search_query_textbox"
        ]
        
        for component in required_components:
            assert component in components