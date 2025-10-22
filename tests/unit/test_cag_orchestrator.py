"""
tests/unit/test_cag_orchestrator.py
-----------------------------------
Unit tests for CAG Orchestrator
Tests the full CAG pipeline integration
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from services.cag_orchestrator_service import CAGOrchestrator, CAGSearchManager
from services.relevance_scorer_service import RelevanceScorer, RelevanceScore
from services.query_rewriter_service import QueryRewriter
from config.cag_settings import CAGSettings


class TestCAGOrchestrator:
    """Test CAG Orchestrator"""
    
    @pytest.fixture
    def mock_repositories(self):
        """Mock repositories"""
        return MagicMock()
    
    @pytest.fixture
    def orchestrator(self, mock_repositories):
        """Initialize orchestrator"""
        return CAGOrchestrator(mock_repositories)
    
    # ================================================================
    # TEST: Initialization
    # ================================================================
    
    @pytest.mark.asyncio
    async def test_initialize(self, orchestrator):
        """Test orchestrator initialization"""
        # Mock the RAG service
        with patch('services.cag_orchestrator_service.RAGSearchService') as mock_rag:
            mock_rag_instance = AsyncMock()
            mock_rag_instance.initialize = AsyncMock()
            mock_rag.return_value = mock_rag_instance
            
            await orchestrator.initialize()
            
            assert orchestrator._initialized is True
            assert orchestrator.scorer is not None
            assert orchestrator.rewriter is not None
    
    @pytest.mark.asyncio
    async def test_check_initialized(self, orchestrator):
        """Test initialization check"""
        from utils.exceptions import ServiceError
        
        # Not initialized
        with pytest.raises(ServiceError):
            orchestrator._check_initialized()
    
    # ================================================================
    # TEST: Search Results Scoring
    # ================================================================
    
    def test_score_results(self, orchestrator):
        """Test scoring search results"""
        results = {
            'deals': [
                {
                    'id': '1',
                    'text': 'Enterprise pricing deal',
                    'similarity': 0.85,
                    'metadata': {'title': 'Deal 1'}
                }
            ],
            'activities': [
                {
                    'id': '2',
                    'text': 'Call about pricing',
                    'similarity': 0.75,
                    'metadata': {'type': 'call'}
                }
            ],
            'agents': []
        }
        
        orchestrator.scorer = RelevanceScorer()
        scored = orchestrator._score_results(results, "pricing", 'deal')
        
        assert len(scored) == 2
        assert all(isinstance(s, RelevanceScore) for s in scored)
    
    def test_score_results_empty(self, orchestrator):
        """Test scoring empty results"""
        results = {'deals': [], 'activities': [], 'agents': []}
        
        orchestrator.scorer = RelevanceScorer()
        scored = orchestrator._score_results(results, "test", 'deal')
        
        assert scored == []
    
    # ================================================================
    # TEST: Correction Decision
    # ================================================================
    
    def test_should_correct_threshold_strategy(self, orchestrator):
        """Test correction decision with threshold strategy"""
        with patch.object(CAGSettings, 'DECISION_STRATEGY', 'threshold'):
            with patch.object(CAGSettings, 'CONFIDENCE_THRESHOLD', 0.6):
                stats = {'average_score': 0.4}
                should_correct = orchestrator._should_correct(stats, [], 'deal')
                assert should_correct is True
                
                stats = {'average_score': 0.8}
                should_correct = orchestrator._should_correct(stats, [], 'deal')
                assert should_correct is False
    
    def test_should_correct_hybrid_strategy(self, orchestrator):
        """Test correction decision with hybrid strategy"""
        with patch.object(CAGSettings, 'DECISION_STRATEGY', 'hybrid'):
            with patch.object(CAGSettings, 'BATCH_QUALITY_THRESHOLD', 0.55):
                with patch.object(CAGSettings, 'MIN_HIGH_QUALITY_RESULTS', 2):
                    # Low score
                    stats = {'average_score': 0.4, 'pass_rate': 0.2}
                    should_correct = orchestrator._should_correct(stats, [], 'deal')
                    assert should_correct is True
                    
                    # Good score but few high-quality
                    stats = {'average_score': 0.7, 'pass_rate': 0.3}
                    should_correct = orchestrator._should_correct(stats, [], 'deal')
                    assert should_correct is True
                    
                    # Good score and results
                    stats = {'average_score': 0.7, 'pass_rate': 0.8}
                    high_quality = [MagicMock(), MagicMock(), MagicMock()]
                    should_correct = orchestrator._should_correct(stats, high_quality, 'deal')
                    assert should_correct is False
    
    def test_should_correct_aggressive_strategy(self, orchestrator):
        """Test correction decision with aggressive strategy"""
        with patch.object(CAGSettings, 'DECISION_STRATEGY', 'aggressive'):
            stats = {'average_score': 0.65}
            should_correct = orchestrator._should_correct(stats, [], 'deal')
            assert should_correct is True
    
    # ================================================================
    # TEST: Query Correction
    # ================================================================
    
    def test_correct_query_with_alternatives(self, orchestrator):
        """Test query correction with alternatives"""
        orchestrator.scorer = RelevanceScorer()
        orchestrator.rewriter = QueryRewriter()
        orchestrator._search_all = MagicMock(return_value={
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
        })
        
        query, results, rewrites = orchestrator._correct_query("test", {}, 5, 'deal')
        
        assert isinstance(query, str)
        assert isinstance(results, dict)
        assert isinstance(rewrites, list)
    
    def test_correct_query_no_alternatives(self, orchestrator):
        """Test query correction when no alternatives generated"""
        orchestrator.rewriter = MagicMock()
        orchestrator.rewriter.rewrite_with_fallback = MagicMock(return_value=[])
        
        query, results, rewrites = orchestrator._correct_query("test", {}, 5, 'deal')
        
        assert query == "test"
        assert rewrites == []
    
    # ================================================================
    # TEST: Search with CAG
    # ================================================================
    
    def test_search_with_cag_no_correction(self, orchestrator):
        """Test CAG search without correction"""
        orchestrator._initialized = True
        orchestrator._search_all = MagicMock(return_value={
            'deals': [
                {
                    'id': '1',
                    'text': 'High quality result',
                    'similarity': 0.9,
                    'metadata': {'title': 'Deal'}
                }
            ],
            'activities': [],
            'agents': []
        })
        orchestrator.scorer = RelevanceScorer()
        orchestrator._should_correct = MagicMock(return_value=False)
        
        result = orchestrator.search_with_cag("test query", 'deal', 5)
        
        assert result['status'] == 'success'
        assert result['correction']['applied'] is False
        assert 'execution_time' in result
    
    def test_search_with_cag_with_correction(self, orchestrator):
        """Test CAG search with correction"""
        orchestrator._initialized = True
        orchestrator._search_all = MagicMock(return_value={
            'deals': [{
                'id': '1',
                'text': 'Result',
                'similarity': 0.5,
                'metadata': {'title': 'Test'}
            }],
            'activities': [],
            'agents': []
        })
        orchestrator.scorer = RelevanceScorer()
        orchestrator._should_correct = MagicMock(return_value=True)
        orchestrator._correct_query = MagicMock(return_value=(
            "corrected",
            {'deals': [], 'activities': [], 'agents': []},
            ["rewrite1"]
        ))
        
        result = orchestrator.search_with_cag("test", 'deal', 5)
        
        assert result['status'] == 'success'
        assert result['correction']['applied'] is True
        assert len(result['correction']['rewrites_used']) > 0
    
    def test_search_with_cag_error_handling(self, orchestrator):
        """Test error handling in CAG search"""
        orchestrator._initialized = True
        orchestrator._search_all = MagicMock(side_effect=Exception("Search failed"))
        
        result = orchestrator.search_with_cag("test", 'deal', 5)
        
        assert result['status'] == 'error'
        assert 'error' in result
    
    # ================================================================
    # TEST: Statistics
    # ================================================================
    
    def test_get_stats(self, orchestrator):
        """Test getting statistics"""
        orchestrator.stats['total_searches'] = 10
        orchestrator.stats['rewrites_triggered'] = 3
        orchestrator.stats['rewrites_successful'] = 2
        
        stats = orchestrator.get_stats()
        
        assert stats['total_searches'] == 10
        assert 'rewrite_rate' in stats
        assert 'success_rate' in stats
    
    def test_reset_stats(self, orchestrator):
        """Test resetting statistics"""
        orchestrator.stats['total_searches'] = 10
        
        orchestrator.reset_stats()
        
        assert orchestrator.stats['total_searches'] == 0
        assert orchestrator.stats['rewrites_triggered'] == 0
    
    # ================================================================
    # TEST: Entity-specific Searches
    # ================================================================
    
    def test_search_all_collections(self, orchestrator):
        """Test searching all collections"""
        orchestrator._initialized = True
        
        # Mock RAG service
        mock_results = {
            'status': 'success',
            'results': {
                'deals': [],
                'activities': [],
                'agents': []
            }
        }
        orchestrator.rag_service = MagicMock()
        orchestrator.rag_service.search = MagicMock(return_value=mock_results)
        orchestrator.scorer = RelevanceScorer()
        orchestrator._should_correct = MagicMock(return_value=False)
        
        result = orchestrator.search_with_cag("test", 'deal', 5)
        
        assert result['status'] == 'success'


class TestCAGSearchManager:
    """Test CAG Search Manager"""
    
    @pytest.fixture
    def mock_orchestrator(self):
        """Mock orchestrator"""
        return MagicMock()
    
    @pytest.fixture
    def manager(self, mock_orchestrator):
        """Initialize manager"""
        return CAGSearchManager(mock_orchestrator)
    
    @pytest.mark.asyncio
    async def test_initialize(self, manager):
        """Test manager initialization"""
        manager.orchestrator.initialize = AsyncMock()
        
        await manager.initialize()
        
        manager.orchestrator.initialize.assert_called_once()
    
    def test_search(self, manager):
        """Test search through manager"""
        mock_result = {
            'status': 'success',
            'results': {'deals': []},
            'correction': {'applied': False}
        }
        manager.orchestrator.search_with_cag = MagicMock(return_value=mock_result)
        
        result = manager.search("test query", document_type='deal')
        
        assert result['status'] == 'success'
        manager.orchestrator.search_with_cag.assert_called_once()
    
    def test_search_without_metadata(self, manager):
        """Test search without metadata"""
        mock_result = {
            'status': 'success',
            'results': {'deals': []},
            'execution_time': 0.1,
            'correction': {'applied': False}
        }
        manager.orchestrator.search_with_cag = MagicMock(return_value=mock_result)
        
        result = manager.search("test", include_metadata=False)
        
        assert 'correction' not in result or result.get('correction') is None
        assert 'results' in result
        assert 'execution_time' in result
    
    def test_search_deals(self, manager):
        """Test deal search"""
        manager.orchestrator.search_with_cag = MagicMock(return_value={
            'status': 'success'
        })
        
        manager.search_deals("pricing")
        
        manager.orchestrator.search_with_cag.assert_called_with(
            "pricing", 'deal', 5
        )
    
    def test_search_activities(self, manager):
        """Test activity search"""
        manager.orchestrator.search_with_cag = MagicMock(return_value={
            'status': 'success'
        })
        
        manager.search_activities("call")
        
        manager.orchestrator.search_with_cag.assert_called_with(
            "call", 'activity', 5
        )
    
    def test_search_agents(self, manager):
        """Test agent search"""
        manager.orchestrator.search_with_cag = MagicMock(return_value={
            'status': 'success'
        })
        
        manager.search_agents("John")
        
        manager.orchestrator.search_with_cag.assert_called_with(
            "John", 'agent', 5
        )
    
    def test_get_stats(self, manager):
        """Test getting stats through manager"""
        mock_stats = {'total_searches': 10}
        manager.orchestrator.get_stats = MagicMock(return_value=mock_stats)
        
        stats = manager.get_stats()
        
        assert stats == mock_stats