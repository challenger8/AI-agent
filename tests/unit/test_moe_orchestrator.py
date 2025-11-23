"""
tests/unit/test_moe_orchestrator.py
-----------------------------------
Unit tests for MoE orchestrator
"""

import pytest
import asyncio
import sys
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from services.moe.moe_orchestrator import MoEOrchestrator
from services.moe.expert_ensemble import EnsembleResult
from config.moe_settings import MoESettings


class TestMoEOrchestratorInit:
    """Tests for MoEOrchestrator initialization"""

    def test_orchestrator_initialization(self):
        """Test orchestrator initializes correctly"""
        orchestrator = MoEOrchestrator()

        assert orchestrator is not None
        assert orchestrator.router is not None
        assert orchestrator.ensemble is not None
        assert len(orchestrator.experts) > 0

    def test_orchestrator_with_services(self):
        """Test orchestrator initializes with services"""
        mock_services = {
            'analytics': Mock(),
            'sentiment': Mock(),
            'deal': Mock()
        }

        orchestrator = MoEOrchestrator(services=mock_services)

        assert orchestrator.services == mock_services

    def test_all_experts_initialized(self):
        """Test all experts are initialized"""
        orchestrator = MoEOrchestrator()

        expected_experts = ['deal_analysis', 'sentiment', 'activity', 'risk_assessment', 'search']

        for expert_type in expected_experts:
            assert expert_type in orchestrator.experts


class TestMoEOrchestratorProcess:
    """Tests for MoEOrchestrator process method"""

    @pytest.fixture
    def orchestrator(self):
        """Create orchestrator instance"""
        return MoEOrchestrator()

    @pytest.mark.asyncio
    async def test_process_returns_ensemble_result(self, orchestrator):
        """Test process returns EnsembleResult"""
        result = await orchestrator.process("Test query")

        assert isinstance(result, EnsembleResult)

    @pytest.mark.asyncio
    async def test_process_contains_routing_info(self, orchestrator):
        """Test process includes routing info when configured"""
        result = await orchestrator.process("Analyze deal 123")

        if MoESettings.INCLUDE_ROUTING_INFO:
            assert 'routing' in result.metadata

    @pytest.mark.asyncio
    async def test_process_updates_metrics(self, orchestrator):
        """Test process updates metrics"""
        initial_count = orchestrator._metrics['total_queries']

        await orchestrator.process("Test query")

        assert orchestrator._metrics['total_queries'] == initial_count + 1

    def test_process_sync(self, orchestrator):
        """Test synchronous process method"""
        result = orchestrator.process_sync("Test query")

        assert isinstance(result, EnsembleResult)

    @pytest.mark.asyncio
    async def test_process_with_context(self, orchestrator):
        """Test process with context"""
        context = {'deal_id': '123'}
        result = await orchestrator.process("Analyze this deal", context)

        assert isinstance(result, EnsembleResult)


class TestMoEOrchestratorExperts:
    """Tests for expert management"""

    @pytest.fixture
    def orchestrator(self):
        """Create orchestrator instance"""
        return MoEOrchestrator()

    def test_get_expert(self, orchestrator):
        """Test getting a specific expert"""
        expert = orchestrator.get_expert('deal_analysis')

        assert expert is not None
        assert expert.expert_type == 'deal_analysis'

    def test_get_nonexistent_expert(self, orchestrator):
        """Test getting a nonexistent expert"""
        expert = orchestrator.get_expert('nonexistent')

        assert expert is None

    def test_get_available_experts(self, orchestrator):
        """Test getting list of available experts"""
        experts = orchestrator.get_available_experts()

        assert isinstance(experts, list)
        assert len(experts) > 0
        assert 'deal_analysis' in experts

    def test_get_expert_descriptions(self, orchestrator):
        """Test getting expert descriptions"""
        descriptions = orchestrator.get_expert_descriptions()

        assert isinstance(descriptions, dict)
        assert 'deal_analysis' in descriptions
        assert len(descriptions['deal_analysis']) > 0


class TestMoEOrchestratorAnalyzeQuery:
    """Tests for query analysis"""

    @pytest.fixture
    def orchestrator(self):
        """Create orchestrator instance"""
        return MoEOrchestrator()

    def test_analyze_query(self, orchestrator):
        """Test analyzing a query without execution"""
        decision = orchestrator.analyze_query("Analyze deal 123")

        assert decision is not None
        assert len(decision.selected_experts) > 0


class TestMoEOrchestratorMetrics:
    """Tests for metrics tracking"""

    @pytest.fixture
    def orchestrator(self):
        """Create orchestrator instance"""
        return MoEOrchestrator()

    def test_get_metrics(self, orchestrator):
        """Test getting metrics"""
        metrics = orchestrator.get_metrics()

        assert 'total_queries' in metrics
        assert 'successful_queries' in metrics
        assert 'router' in metrics
        assert 'ensemble' in metrics
        assert 'experts' in metrics

    def test_reset_metrics(self, orchestrator):
        """Test resetting metrics"""
        orchestrator._metrics['total_queries'] = 100
        orchestrator.reset_metrics()

        metrics = orchestrator.get_metrics()
        assert metrics['total_queries'] == 0

    @pytest.mark.asyncio
    async def test_metrics_after_process(self, orchestrator):
        """Test metrics are updated after processing"""
        await orchestrator.process("Test query")

        metrics = orchestrator.get_metrics()
        assert metrics['total_queries'] == 1


class TestMoEOrchestratorSettings:
    """Tests for settings access"""

    @pytest.fixture
    def orchestrator(self):
        """Create orchestrator instance"""
        return MoEOrchestrator()

    def test_get_settings(self, orchestrator):
        """Test getting current settings"""
        settings = orchestrator.get_settings()

        assert isinstance(settings, dict)
        assert 'routing_strategy' in settings
        assert 'ensemble_strategy' in settings


class TestMoEOrchestratorErrorHandling:
    """Tests for error handling"""

    @pytest.fixture
    def orchestrator(self):
        """Create orchestrator instance"""
        return MoEOrchestrator()

    @pytest.mark.asyncio
    async def test_process_handles_expert_errors(self, orchestrator):
        """Test process handles expert errors gracefully"""
        # Even if experts fail, process should return a result
        result = await orchestrator.process("Invalid query that might cause errors")

        assert isinstance(result, EnsembleResult)

    @pytest.mark.asyncio
    async def test_process_empty_query(self, orchestrator):
        """Test process with empty query"""
        result = await orchestrator.process("")

        assert isinstance(result, EnsembleResult)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
