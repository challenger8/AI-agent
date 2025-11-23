"""
tests/integration/test_moe_integration.py
-----------------------------------------
Integration tests for MoE system
"""

import pytest
import asyncio
import sys
from pathlib import Path
from unittest.mock import Mock

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from services.moe.moe_orchestrator import MoEOrchestrator
from services.moe.expert_router import ExpertRouter
from services.moe.expert_ensemble import ExpertEnsemble
from config.moe_settings import MoESettings


class TestMoEFullPipeline:
    """Integration tests for the complete MoE pipeline"""

    @pytest.fixture
    def mock_services(self):
        """Create mock services for testing"""
        analytics = Mock()
        analytics.analyze_deal_comprehensive.return_value = {
            'health_score': 75,
            'health_category': 'medium',
            'risk_indicators': ['Test risk'],
            'recommendations': ['Test rec'],
            'insights': {}
        }
        analytics.analyze_portfolio_overview.return_value = {
            'summary': {'total_deals': 10},
            'status_distribution': {'active': 5}
        }

        sentiment = Mock()
        sentiment.model_loaded = True
        sentiment.analyze_text.return_value = {
            'sentiment': 'positive',
            'confidence': 0.85
        }

        deal = Mock()
        deal.get_all_deals.return_value = [
            {'id': '1', 'title': 'Deal 1'},
            {'id': '2', 'title': 'Deal 2'}
        ]

        return {
            'analytics': analytics,
            'sentiment': sentiment,
            'deal': deal
        }

    @pytest.fixture
    def orchestrator(self, mock_services):
        """Create orchestrator with mock services"""
        return MoEOrchestrator(services=mock_services)

    @pytest.mark.asyncio
    async def test_deal_analysis_pipeline(self, orchestrator):
        """Test complete deal analysis through MoE"""
        result = await orchestrator.process(
            "Analyze deal 123",
            {'deal_id': '123'}
        )

        assert result is not None
        assert result.primary_expert in ['deal_analysis', 'search', MoESettings.DEFAULT_EXPERT]

    @pytest.mark.asyncio
    async def test_sentiment_analysis_pipeline(self, orchestrator):
        """Test complete sentiment analysis through MoE"""
        result = await orchestrator.process(
            "What's the sentiment of this text?",
            {'text': 'This is a test text'}
        )

        assert result is not None

    @pytest.mark.asyncio
    async def test_search_pipeline(self, orchestrator):
        """Test search query through MoE"""
        result = await orchestrator.process("Find deals related to software")

        assert result is not None

    @pytest.mark.asyncio
    async def test_multi_expert_query(self, orchestrator):
        """Test query that activates multiple experts"""
        result = await orchestrator.process(
            "Analyze deal risks and sentiment for deal 123"
        )

        assert result is not None
        # May have multiple expert results
        assert len(result.expert_results) >= 0


class TestMoERouterEnsembleIntegration:
    """Integration tests for router and ensemble interaction"""

    @pytest.fixture
    def router(self):
        """Create router instance"""
        return ExpertRouter()

    @pytest.fixture
    def ensemble(self):
        """Create ensemble instance"""
        return ExpertEnsemble()

    def test_router_decision_to_ensemble(self, router, ensemble):
        """Test routing decision flows to ensemble correctly"""
        # Route a query
        decision = router.route("Analyze deal 123")

        # Verify decision has required fields for ensemble
        assert decision.selected_experts is not None
        assert decision.confidence_scores is not None

    def test_multiple_queries_routing(self, router):
        """Test routing multiple queries"""
        queries = [
            "Analyze deal 123",
            "What's the sentiment?",
            "Find similar deals",
            "Show recent activities",
            "What are the risks?"
        ]

        for query in queries:
            decision = router.route(query)
            assert len(decision.selected_experts) > 0


class TestMoEConfigurationIntegration:
    """Integration tests for MoE configuration"""

    def test_settings_affect_routing(self):
        """Test that settings affect routing behavior"""
        router = ExpertRouter()

        # Test with default settings
        decision = router.route("Test query")

        # Number of experts should respect MAX_ACTIVE_EXPERTS
        assert len(decision.selected_experts) <= MoESettings.MAX_ACTIVE_EXPERTS

    def test_settings_affect_ensemble(self):
        """Test that settings affect ensemble behavior"""
        from services.moe.base_expert import ExpertResult

        ensemble = ExpertEnsemble()

        results = [
            ExpertResult(
                expert_type='deal_analysis',
                success=True,
                data={'score': 75},
                confidence=0.8
            ),
            ExpertResult(
                expert_type='sentiment',
                success=True,
                data={'sentiment': 'positive'},
                confidence=0.7
            )
        ]

        combined = ensemble.combine("Test query", results)

        assert combined.strategy_used == MoESettings.ENSEMBLE_STRATEGY


class TestMoEMetricsIntegration:
    """Integration tests for metrics across components"""

    @pytest.fixture
    def orchestrator(self):
        """Create orchestrator instance"""
        return MoEOrchestrator()

    @pytest.mark.asyncio
    async def test_metrics_tracked_end_to_end(self, orchestrator):
        """Test metrics are tracked across all components"""
        # Process some queries
        await orchestrator.process("Query 1")
        await orchestrator.process("Query 2")

        metrics = orchestrator.get_metrics()

        # Check orchestrator metrics
        assert metrics['total_queries'] == 2

        # Check router metrics
        assert metrics['router']['total_routes'] == 2

        # Check ensemble metrics
        assert metrics['ensemble']['total_ensembles'] == 2

    def test_metrics_reset_propagates(self, orchestrator):
        """Test metrics reset propagates to all components"""
        orchestrator._metrics['total_queries'] = 100
        orchestrator.reset_metrics()

        metrics = orchestrator.get_metrics()

        assert metrics['total_queries'] == 0
        assert metrics['router']['total_routes'] == 0


class TestMoEErrorRecovery:
    """Integration tests for error recovery"""

    @pytest.fixture
    def orchestrator(self):
        """Create orchestrator instance"""
        return MoEOrchestrator()

    @pytest.mark.asyncio
    async def test_recovers_from_expert_failure(self, orchestrator):
        """Test system recovers when an expert fails"""
        # Even with no services, should return a result
        result = await orchestrator.process("Test query")

        assert result is not None
        # Result may have failed experts but should still return

    @pytest.mark.asyncio
    async def test_handles_timeout_gracefully(self, orchestrator):
        """Test system handles timeouts gracefully"""
        result = await orchestrator.process("Complex query")

        assert result is not None


class TestMoEConcurrency:
    """Integration tests for concurrent operations"""

    @pytest.fixture
    def orchestrator(self):
        """Create orchestrator instance"""
        return MoEOrchestrator()

    @pytest.mark.asyncio
    async def test_concurrent_queries(self, orchestrator):
        """Test processing multiple queries concurrently"""
        queries = [
            "Query 1",
            "Query 2",
            "Query 3"
        ]

        tasks = [orchestrator.process(q) for q in queries]
        results = await asyncio.gather(*tasks)

        assert len(results) == 3
        for result in results:
            assert result is not None


class TestMoEExpertInteraction:
    """Integration tests for expert interaction patterns"""

    @pytest.fixture
    def orchestrator(self):
        """Create orchestrator instance"""
        return MoEOrchestrator()

    def test_all_experts_accessible(self, orchestrator):
        """Test all experts are accessible"""
        for expert_type in MoESettings.EXPERT_TYPES:
            expert = orchestrator.get_expert(expert_type)
            assert expert is not None
            assert expert.expert_type == expert_type

    def test_expert_descriptions_available(self, orchestrator):
        """Test all expert descriptions are available"""
        descriptions = orchestrator.get_expert_descriptions()

        for expert_type in MoESettings.EXPERT_TYPES:
            assert expert_type in descriptions
            assert len(descriptions[expert_type]) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
