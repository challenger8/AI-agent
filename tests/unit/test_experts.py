"""
tests/unit/test_experts.py
--------------------------
Unit tests for MoE expert implementations
"""

import pytest
import asyncio
import sys
from pathlib import Path
from unittest.mock import Mock, AsyncMock

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from services.moe.base_expert import BaseExpert, ExpertResult
from services.moe.experts.deal_analysis_expert import DealAnalysisExpert
from services.moe.experts.sentiment_expert import SentimentExpert
from services.moe.experts.activity_expert import ActivityExpert
from services.moe.experts.risk_assessment_expert import RiskAssessmentExpert
from services.moe.experts.search_expert import SearchExpert


class TestExpertResult:
    """Tests for ExpertResult dataclass"""

    def test_expert_result_creation(self):
        """Test creating an ExpertResult"""
        result = ExpertResult(
            expert_type='deal_analysis',
            success=True,
            data={'health_score': 75},
            confidence=0.85,
            reasoning='Test reasoning'
        )

        assert result.expert_type == 'deal_analysis'
        assert result.success
        assert result.confidence == 0.85

    def test_expert_result_to_dict(self):
        """Test ExpertResult serialization"""
        result = ExpertResult(
            expert_type='deal_analysis',
            success=True,
            data={'health_score': 75},
            confidence=0.85
        )

        result_dict = result.to_dict()

        assert 'expert_type' in result_dict
        assert 'success' in result_dict
        assert 'confidence' in result_dict

    def test_expert_result_from_dict(self):
        """Test ExpertResult deserialization"""
        data = {
            'expert_type': 'deal_analysis',
            'success': True,
            'data': {'health_score': 75},
            'confidence': 0.85
        }

        result = ExpertResult.from_dict(data)

        assert result.expert_type == 'deal_analysis'
        assert result.confidence == 0.85

    def test_expert_result_error(self):
        """Test creating error result"""
        result = ExpertResult.error_result('deal_analysis', 'Test error')

        assert not result.success
        assert result.confidence == 0.0
        assert 'error' in result.data

    def test_is_high_confidence(self):
        """Test high confidence check"""
        high = ExpertResult(
            expert_type='test',
            success=True,
            data={},
            confidence=0.8
        )

        low = ExpertResult(
            expert_type='test',
            success=True,
            data={},
            confidence=0.5
        )

        assert high.is_high_confidence()
        assert not low.is_high_confidence()


class TestDealAnalysisExpert:
    """Tests for DealAnalysisExpert"""

    @pytest.fixture
    def expert(self):
        """Create expert instance"""
        return DealAnalysisExpert()

    def test_expert_type(self, expert):
        """Test expert type property"""
        assert expert.expert_type == 'deal_analysis'

    def test_expert_description(self, expert):
        """Test expert description"""
        assert len(expert.description) > 0

    def test_can_handle_deal_query(self, expert):
        """Test can_handle for deal queries"""
        score = expert.can_handle("Analyze deal 123")
        assert score > 0

    def test_can_handle_non_deal_query(self, expert):
        """Test can_handle for non-deal queries"""
        score = expert.can_handle("What's the weather?")
        assert score < 0.5

    @pytest.mark.asyncio
    async def test_analyze_no_service(self, expert):
        """Test analyze with no analytics service"""
        result = await expert.analyze("Analyze deal 123")

        assert not result.success
        assert 'error' in result.data

    @pytest.mark.asyncio
    async def test_analyze_with_mock_service(self, expert):
        """Test analyze with mocked analytics service"""
        mock_analytics = Mock()
        mock_analytics.analyze_deal_comprehensive.return_value = {
            'health_score': 75,
            'health_category': 'medium',
            'risk_indicators': [],
            'recommendations': []
        }

        expert.services = {'analytics': mock_analytics}

        result = await expert.analyze("Analyze deal 123", {'deal_id': '123'})

        assert result.success
        assert result.data['health_score'] == 75


class TestSentimentExpert:
    """Tests for SentimentExpert"""

    @pytest.fixture
    def expert(self):
        """Create expert instance"""
        return SentimentExpert()

    def test_expert_type(self, expert):
        """Test expert type property"""
        assert expert.expert_type == 'sentiment'

    def test_can_handle_sentiment_query(self, expert):
        """Test can_handle for sentiment queries"""
        score = expert.can_handle("What's the sentiment?")
        assert score > 0

    def test_can_handle_persian_text(self, expert):
        """Test can_handle for Persian text"""
        # Persian text should get a boost
        score = expert.can_handle("این متن را تحلیل کن")
        assert score > 0

    @pytest.mark.asyncio
    async def test_analyze_no_service(self, expert):
        """Test analyze with no sentiment service"""
        result = await expert.analyze("Test text")

        assert not result.success


class TestActivityExpert:
    """Tests for ActivityExpert"""

    @pytest.fixture
    def expert(self):
        """Create expert instance"""
        return ActivityExpert()

    def test_expert_type(self, expert):
        """Test expert type property"""
        assert expert.expert_type == 'activity'

    def test_can_handle_activity_query(self, expert):
        """Test can_handle for activity queries"""
        score = expert.can_handle("Show recent activities")
        assert score > 0

    def test_can_handle_timeline_query(self, expert):
        """Test can_handle for timeline queries"""
        score = expert.can_handle("What happened last week?")
        assert score > 0


class TestRiskAssessmentExpert:
    """Tests for RiskAssessmentExpert"""

    @pytest.fixture
    def expert(self):
        """Create expert instance"""
        return RiskAssessmentExpert()

    def test_expert_type(self, expert):
        """Test expert type property"""
        assert expert.expert_type == 'risk_assessment'

    def test_can_handle_risk_query(self, expert):
        """Test can_handle for risk queries"""
        score = expert.can_handle("What are the risks?")
        assert score > 0

    def test_can_handle_warning_query(self, expert):
        """Test can_handle for warning queries"""
        score = expert.can_handle("Show me warnings")
        assert score > 0


class TestSearchExpert:
    """Tests for SearchExpert"""

    @pytest.fixture
    def expert(self):
        """Create expert instance"""
        return SearchExpert()

    def test_expert_type(self, expert):
        """Test expert type property"""
        assert expert.expert_type == 'search'

    def test_can_handle_search_query(self, expert):
        """Test can_handle for search queries"""
        score = expert.can_handle("Find deals related to software")
        assert score > 0

    def test_can_handle_question(self, expert):
        """Test can_handle for questions"""
        score = expert.can_handle("Where can I find...?")
        assert score > 0

    def test_default_minimum_score(self, expert):
        """Test search expert has minimum score (fallback)"""
        score = expert.can_handle("random text")
        assert score >= 0.3  # Search is often the fallback


class TestExpertMetrics:
    """Tests for expert metrics tracking"""

    @pytest.fixture
    def expert(self):
        """Create expert instance"""
        return DealAnalysisExpert()

    def test_initial_metrics(self, expert):
        """Test initial metrics are zero"""
        metrics = expert.get_metrics()

        assert metrics['total_calls'] == 0
        assert metrics['successful_calls'] == 0

    def test_reset_metrics(self, expert):
        """Test resetting metrics"""
        expert._metrics['total_calls'] = 10
        expert.reset_metrics()

        metrics = expert.get_metrics()
        assert metrics['total_calls'] == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
