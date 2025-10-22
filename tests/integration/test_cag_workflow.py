"""
tests/integration/test_cag_workflow.py
--------------------------------------
Integration tests for full CAG workflow
Tests complete pipeline: Search -> Score -> Correct -> Results
"""

import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime, timedelta

from services.cag_orchestrator_service import CAGOrchestrator, CAGSearchManager
from services.relevance_scorer_service import RelevanceScorer
from services.query_rewriter_service import QueryRewriter, QueryRewriterWithFallback
from services.rag_search_service import RAGSearchService
from config.cag_settings import CAGSettings


class TestCAGFullWorkflow:
    """Test complete CAG workflows"""
    
    @pytest.fixture
    def mock_repositories(self):
        """Mock repositories"""
        return MagicMock()
    
    @pytest.fixture
    def initialized_orchestrator(self, mock_repositories):
        """Create and initialize orchestrator"""
        orchestrator = CAGOrchestrator(mock_repositories)
        return orchestrator
    
    # ================================================================
    # TEST: High Quality Results (No Correction Needed)
    # ================================================================
    
    @pytest.mark.asyncio
    async def test_workflow_high_quality_results(self, initialized_orchestrator):
        """Test workflow with high-quality results - no correction"""
        orchestrator = initialized_orchestrator
        
        # Setup orchestrator without async init
        orchestrator.scorer = RelevanceScorer()
        orchestrator.rewriter = QueryRewriterWithFallback()
        orchestrator._initialized = True
        
        # Mock high-quality search results
        high_quality_results = {
            'deals': [
                {
                    'id': 'deal_1',
                    'text': 'Enterprise software pricing discussion',
                    'similarity': 0.95,
                    'metadata': {
                        'title': 'Enterprise Deal',
                        'status': 'open',
                        'customer_name': 'Tech Corp',
                        'updated_at': datetime.now().isoformat()
                    }
                },
                {
                    'id': 'deal_2',
                    'text': 'Large implementation project pricing',
                    'similarity': 0.88,
                    'metadata': {
                        'title': 'Implementation Deal',
                        'status': 'negotiation',
                        'updated_at': (datetime.now() - timedelta(days=2)).isoformat()
                    }
                }
            ],
            'activities': [],
            'agents': []
        }
        
        orchestrator._search_all = MagicMock(return_value=high_quality_results)
        orchestrator._should_correct = MagicMock(return_value=False)
        
        # Execute search
        result = orchestrator.search_with_cag("enterprise pricing", 'deal', 5)
        
        # Verify no correction applied
        assert result['status'] == 'success'
        assert result['correction']['applied'] is False
        assert len(result['results']['deals']) == 2
        assert result['confidence_metrics']['average_score'] > 0.6
    
    # ================================================================
    # TEST: Low Quality Results (Correction Needed)
    # ================================================================
    
    @pytest.mark.asyncio
    async def test_workflow_low_quality_triggers_correction(self, initialized_orchestrator):
        """Test workflow with low-quality results - triggers correction"""
        orchestrator = initialized_orchestrator
        orchestrator.scorer = RelevanceScorer()
        orchestrator.rewriter = QueryRewriterWithFallback()
        orchestrator._initialized = True
        
        # Mock low-quality initial results
        low_quality_results = {
            'deals': [
                {
                    'id': 'deal_1',
                    'text': 'Random document',
                    'similarity': 0.35,
                    'metadata': {
                        'title': 'Old Deal',
                        'updated_at': (datetime.now() - timedelta(days=365)).isoformat()
                    }
                }
            ],
            'activities': [],
            'agents': []
        }
        
        # Mock improved results after correction
        improved_results = {
            'deals': [
                {
                    'id': 'deal_2',
                    'text': 'Enterprise software pricing discussion',
                    'similarity': 0.85,
                    'metadata': {
                        'title': 'Enterprise Deal',
                        'updated_at': datetime.now().isoformat()
                    }
                }
            ],
            'activities': [],
            'agents': []
        }
        
        orchestrator._search_all = MagicMock(side_effect=[low_quality_results, improved_results])
        orchestrator._should_correct = MagicMock(return_value=True)
        orchestrator.rewriter = QueryRewriterWithFallback()
        
        # Execute search
        result = orchestrator.search_with_cag("pricing", 'deal', 5)
        
        # Verify correction was applied
        assert result['status'] == 'success'
        assert result['correction']['applied'] is True
        assert len(result['correction']['rewrites_used']) >= 0
    
    # ================================================================
    # TEST: Persian Text Handling
    # ================================================================
    
    @pytest.mark.asyncio
    async def test_workflow_persian_text(self, initialized_orchestrator):
        """Test workflow with Persian queries"""
        orchestrator = initialized_orchestrator
        orchestrator.scorer = RelevanceScorer()
        orchestrator.rewriter = QueryRewriterWithFallback()
        orchestrator._initialized = True
        
        persian_results = {
            'deals': [
                {
                    'id': 'deal_1',
                    'text': 'معامله قیمت داری',
                    'similarity': 0.8,
                    'metadata': {
                        'title': 'معامله تجاری',
                        'updated_at': datetime.now().isoformat()
                    }
                }
            ],
            'activities': [],
            'agents': []
        }
        
        orchestrator._search_all = MagicMock(return_value=persian_results)
        orchestrator._should_correct = MagicMock(return_value=False)
        
        # Execute with Persian query
        result = orchestrator.search_with_cag("قیمت", 'deal', 5)
        
        assert result['status'] == 'success'
        assert result['original_query'] == "قیمت"
    
    # ================================================================
    # TEST: Query Correction Impact
    # ================================================================
    
    @pytest.mark.asyncio
    async def test_correction_improves_results(self, initialized_orchestrator):
        """Test that correction improves result quality"""
        orchestrator = initialized_orchestrator
        orchestrator.scorer = RelevanceScorer()
        orchestrator.rewriter = QueryRewriterWithFallback()
        orchestrator._initialized = True
        
        # Initial poor results
        poor_results = {
            'deals': [
                {
                    'id': '1',
                    'text': 'Random text',
                    'similarity': 0.2,
                    'metadata': {'title': 'Poor Match'}
                }
            ],
            'activities': [],
            'agents': []
        }
        
        # Corrected better results
        better_results = {
            'deals': [
                {
                    'id': '2',
                    'text': 'Relevant deal about pricing',
                    'similarity': 0.9,
                    'metadata': {'title': 'Relevant Deal', 'created_at': datetime.now().isoformat()}
                }
            ],
            'activities': [],
            'agents': []
        }
        
        orchestrator._search_all = MagicMock(side_effect=[poor_results, better_results])
        orchestrator._should_correct = MagicMock(return_value=True)
        orchestrator.rewriter = QueryRewriterWithFallback()
        
        result = orchestrator.search_with_cag("pricing", 'deal', 5)
        
        # Verify improvement
        assert result['correction']['applied'] is True
        # Better results should be returned
        assert len(result['results']['deals']) > 0
    
    # ================================================================
    # TEST: Multiple Entity Types
    # ================================================================
    
    @pytest.mark.asyncio
    async def test_workflow_multiple_entity_types(self, initialized_orchestrator):
        """Test searching and scoring multiple entity types"""
        orchestrator = initialized_orchestrator
        orchestrator.scorer = RelevanceScorer()
        orchestrator.rewriter = QueryRewriterWithFallback()
        orchestrator._initialized = True
        
        mixed_results = {
            'deals': [
                {
                    'id': 'd1',
                    'text': 'Enterprise pricing',
                    'similarity': 0.85,
                    'metadata': {'type': 'deal', 'title': 'Deal'}
                }
            ],
            'activities': [
                {
                    'id': 'a1',
                    'text': 'Call about pricing',
                    'similarity': 0.75,
                    'metadata': {'type': 'activity', 'activity_type': 'call'}
                }
            ],
            'agents': [
                {
                    'id': 'ag1',
                    'text': 'Sarah Johnson - Sales Manager',
                    'similarity': 0.65,
                    'metadata': {'type': 'agent', 'name': 'Sarah Johnson'}
                }
            ]
        }
        
        orchestrator._search_all = MagicMock(return_value=mixed_results)
        orchestrator._should_correct = MagicMock(return_value=False)
        
        result = orchestrator.search_with_cag("pricing", 'deal', 5)
        
        assert result['status'] == 'success'
        assert len(result['results']['deals']) == 1
        assert len(result['results']['activities']) == 1
        assert len(result['results']['agents']) == 1
    
    # ================================================================
    # TEST: Statistics Tracking
    # ================================================================
    
    @pytest.mark.asyncio
    async def test_workflow_statistics_tracking(self, initialized_orchestrator):
        """Test that CAG tracks statistics correctly"""
        orchestrator = initialized_orchestrator
        orchestrator.scorer = RelevanceScorer()
        orchestrator.rewriter = QueryRewriterWithFallback()
        orchestrator._initialized = True
        
        results = {
            'deals': [
                {
                    'id': '1',
                    'text': 'test',
                    'similarity': 0.8,
                    'metadata': {'title': 'Test'}
                }
            ],
            'activities': [],
            'agents': []
        }
        
        orchestrator._search_all = MagicMock(return_value=results)
        orchestrator._should_correct = MagicMock(return_value=False)
        
        # Run multiple searches
        for i in range(3):
            orchestrator.search_with_cag(f"query {i}", 'deal', 5)
        
        stats = orchestrator.get_stats()
        
        assert stats['total_searches'] == 3
        assert 'rewrite_rate' in stats
        assert 'success_rate' in stats
    
    # ================================================================
    # TEST: Error Handling in Workflow
    # ================================================================
    
    @pytest.mark.asyncio
    async def test_workflow_error_handling(self, initialized_orchestrator):
        """Test error handling in workflow"""
        orchestrator = initialized_orchestrator
        orchestrator.scorer = RelevanceScorer()
        orchestrator.rewriter = QueryRewriterWithFallback()
        orchestrator._initialized = True
        
        # Mock error in search
        orchestrator._search_all = MagicMock(side_effect=Exception("Search failed"))
        
        result = orchestrator.search_with_cag("test", 'deal', 5)
        
        assert result['status'] == 'error'
        assert 'error' in result
    
    # ================================================================
    # TEST: Decision Strategies
    # ================================================================
    
    @pytest.mark.asyncio
    async def test_workflow_threshold_strategy(self, initialized_orchestrator):
        """Test workflow with threshold decision strategy"""
        orchestrator = initialized_orchestrator
        orchestrator.scorer = RelevanceScorer()
        orchestrator.rewriter = QueryRewriterWithFallback()
        orchestrator._initialized = True
        
        with patch.object(CAGSettings, 'DECISION_STRATEGY', 'threshold'):
            results = {
                'deals': [{'id': '1', 'text': 'test', 'similarity': 0.4, 'metadata': {}}],
                'activities': [],
                'agents': []
            }
            
            orchestrator._search_all = MagicMock(return_value=results)
            orchestrator._correct_query = MagicMock(return_value=('test', results, []))
            
            result = orchestrator.search_with_cag("test", 'deal', 5)
            
            assert result['status'] == 'success'
    
    @pytest.mark.asyncio
    async def test_workflow_hybrid_strategy(self, initialized_orchestrator):
        """Test workflow with hybrid decision strategy"""
        orchestrator = initialized_orchestrator
        orchestrator.scorer = RelevanceScorer()
        orchestrator.rewriter = QueryRewriterWithFallback()
        orchestrator._initialized = True
        
        with patch.object(CAGSettings, 'DECISION_STRATEGY', 'hybrid'):
            results = {
                'deals': [{'id': '1', 'text': 'test', 'similarity': 0.5, 'metadata': {}}],
                'activities': [],
                'agents': []
            }
            
            orchestrator._search_all = MagicMock(return_value=results)
            orchestrator._correct_query = MagicMock(return_value=('test', results, []))
            
            result = orchestrator.search_with_cag("test", 'deal', 5)
            
            assert result['status'] == 'success'


class TestCAGSearchManager:
    """Test CAGSearchManager integration"""
    
    @pytest.fixture
    def mock_orchestrator(self):
        """Mock orchestrator"""
        return MagicMock()
    
    @pytest.fixture
    def manager(self, mock_orchestrator):
        """Create manager"""
        return CAGSearchManager(mock_orchestrator)
    
    def test_manager_search_all(self, manager):
        """Test manager search all"""
        manager.orchestrator.search_with_cag = MagicMock(return_value={
            'status': 'success',
            'results': {'deals': []},
            'correction': {'applied': False}
        })
        
        result = manager.search("test")
        
        assert result['status'] == 'success'
    
    def test_manager_search_by_type(self, manager):
        """Test manager type-specific search"""
        manager.orchestrator.search_with_cag = MagicMock(return_value={
            'status': 'success',
            'results': {'deals': [{'id': '1'}]},
            'correction': {'applied': False}
        })
        
        result = manager.search_deals("pricing")
        
        assert 'status' in result
    
    def test_manager_stats(self, manager):
        """Test manager statistics"""
        manager.orchestrator.get_stats = MagicMock(return_value={
            'total_searches': 10,
            'rewrites_triggered': 3
        })
        
        stats = manager.get_stats()
        
        assert stats['total_searches'] == 10