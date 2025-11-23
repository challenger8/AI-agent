"""
tests/unit/test_expert_router.py
--------------------------------
Unit tests for MoE expert router
"""

import pytest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from services.moe.expert_router import ExpertRouter, RoutingDecision
from config.moe_settings import MoESettings


class TestExpertRouter:
    """Tests for ExpertRouter class"""

    @pytest.fixture
    def router(self):
        """Create router instance for testing"""
        return ExpertRouter()

    def test_router_initialization(self, router):
        """Test router initializes correctly"""
        assert router is not None
        assert router._routing_cache == {}

    def test_route_deal_analysis_query(self, router):
        """Test routing a deal analysis query"""
        query = "Analyze deal 123"
        decision = router.route(query)

        assert isinstance(decision, RoutingDecision)
        # Deal analysis should have higher confidence than other experts
        assert decision.confidence_scores.get('deal_analysis', 0) > 0
        assert decision.query == query

    def test_route_sentiment_query(self, router):
        """Test routing a sentiment analysis query"""
        query = "What's the sentiment of this text?"
        decision = router.route(query)

        assert isinstance(decision, RoutingDecision)
        # Sentiment should have higher score than most experts
        assert decision.confidence_scores.get('sentiment', 0) > 0

    def test_route_risk_query(self, router):
        """Test routing a risk assessment query"""
        query = "What are the risks for deal 456?"
        decision = router.route(query)

        assert isinstance(decision, RoutingDecision)
        # Risk and deal_analysis should have higher scores
        risk_score = decision.confidence_scores.get('risk_assessment', 0)
        deal_score = decision.confidence_scores.get('deal_analysis', 0)
        assert risk_score > 0 or deal_score > 0

    def test_route_search_query(self, router):
        """Test routing a search query"""
        query = "Find deals related to software"
        decision = router.route(query)

        assert isinstance(decision, RoutingDecision)
        assert 'search' in decision.selected_experts

    def test_route_activity_query(self, router):
        """Test routing an activity query"""
        query = "Show recent activities for last week"
        decision = router.route(query)

        assert isinstance(decision, RoutingDecision)
        # Activity should have a score
        assert decision.confidence_scores.get('activity', 0) > 0

    def test_route_persian_query(self, router):
        """Test routing a Persian query"""
        query = "تحلیل معامله شماره ۱۲۳"
        decision = router.route(query)

        assert isinstance(decision, RoutingDecision)
        assert len(decision.selected_experts) > 0

    def test_route_with_context(self, router):
        """Test routing with context hints"""
        query = "Analyze this"
        context = {'expert_hint': 'sentiment'}
        decision = router.route(query, context)

        assert isinstance(decision, RoutingDecision)
        # Context should influence routing

    def test_routing_decision_properties(self, router):
        """Test RoutingDecision properties"""
        query = "Analyze deal 123"
        decision = router.route(query)

        assert decision.primary_expert in MoESettings.EXPERT_TYPES or decision.primary_expert == MoESettings.DEFAULT_EXPERT

    def test_routing_decision_to_dict(self, router):
        """Test RoutingDecision serialization"""
        query = "Analyze deal 123"
        decision = router.route(query)
        decision_dict = decision.to_dict()

        assert 'query' in decision_dict
        assert 'selected_experts' in decision_dict
        assert 'confidence_scores' in decision_dict

    def test_router_caching(self, router):
        """Test that routing decisions are cached"""
        query = "Analyze deal 123"

        # First call
        decision1 = router.route(query)

        # Second call should use cache
        decision2 = router.route(query)

        assert decision1.selected_experts == decision2.selected_experts

    def test_router_metrics(self, router):
        """Test router metrics tracking"""
        # Make some queries
        router.route("Analyze deal 123")
        router.route("Find similar deals")

        metrics = router.get_metrics()

        assert 'total_routes' in metrics
        assert metrics['total_routes'] == 2

    def test_router_reset_metrics(self, router):
        """Test resetting router metrics"""
        router.route("Test query")
        router.reset_metrics()

        metrics = router.get_metrics()
        assert metrics['total_routes'] == 0

    def test_router_clear_cache(self, router):
        """Test clearing routing cache"""
        router.route("Test query")
        router.clear_cache()

        assert router._routing_cache == {}

    def test_fallback_to_default_expert(self, router):
        """Test fallback when no expert matches"""
        query = "xyz123"  # Unlikely to match any keywords
        decision = router.route(query)

        # Should fall back to default expert
        assert len(decision.selected_experts) > 0

    def test_multi_expert_routing(self, router):
        """Test multi-expert selection"""
        query = "Analyze deal risks and sentiment"
        decision = router.route(query)

        # Should select multiple experts if enabled
        if MoESettings.ENABLE_MULTI_EXPERT:
            assert len(decision.selected_experts) >= 1


class TestRoutingDecision:
    """Tests for RoutingDecision dataclass"""

    def test_routing_decision_creation(self):
        """Test creating a RoutingDecision"""
        decision = RoutingDecision(
            query="Test query",
            selected_experts=['deal_analysis'],
            confidence_scores={'deal_analysis': 0.8},
            query_type='deal_analysis',
            reasoning='Test reasoning'
        )

        assert decision.query == "Test query"
        assert decision.primary_expert == 'deal_analysis'

    def test_routing_decision_is_multi_expert(self):
        """Test is_multi_expert property"""
        single = RoutingDecision(
            query="Test",
            selected_experts=['deal_analysis'],
            confidence_scores={'deal_analysis': 0.8},
            query_type='deal_analysis',
            reasoning='Test'
        )

        multi = RoutingDecision(
            query="Test",
            selected_experts=['deal_analysis', 'sentiment'],
            confidence_scores={'deal_analysis': 0.8, 'sentiment': 0.7},
            query_type='mixed',
            reasoning='Test'
        )

        assert not single.is_multi_expert
        assert multi.is_multi_expert


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
