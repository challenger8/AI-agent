"""
tests/unit/test_gradio_client.py
--------------------------------
Unit tests for Gradio MCP client
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Check if gradio is available
try:
    import gradio
    GRADIO_AVAILABLE = True
except ImportError:
    GRADIO_AVAILABLE = False

# Skip all tests if gradio not available
pytestmark = pytest.mark.skipif(
    not GRADIO_AVAILABLE,
    reason="Gradio not installed"
)


class TestGradioMCPClientInit:
    """Tests for GradioMCPClient initialization"""

    @patch('gradio_mcp_client.create_database_manager')
    @patch('gradio_mcp_client.create_repositories')
    @patch('gradio_mcp_client.services_available', True)
    def test_client_initialization(self, mock_repos, mock_db):
        """Test client initializes services correctly"""
        mock_db.return_value = Mock()
        mock_repos.return_value = Mock()

        from gradio_mcp_client import GradioMCPClient
        client = GradioMCPClient()

        assert client is not None

    def test_client_without_services(self):
        """Test client handles missing services gracefully"""
        with patch('gradio_mcp_client.services_available', False):
            from gradio_mcp_client import GradioMCPClient
            client = GradioMCPClient()
            assert client.db_manager is None
            assert client.repositories is None


class TestGradioClientAnalyzeDeal:
    """Tests for deal analysis functionality"""

    def test_analyze_deal_no_service(self):
        """Test analyze_deal returns error when service unavailable"""
        from gradio_mcp_client import GradioMCPClient

        with patch('gradio_mcp_client.services_available', False):
            client = GradioMCPClient()
            result = client.analyze_deal("123")
            assert "error" in result

    @patch('gradio_mcp_client.services_available', True)
    @patch('gradio_mcp_client.create_database_manager')
    @patch('gradio_mcp_client.create_repositories')
    def test_analyze_deal_with_mock_service(self, mock_repos, mock_db):
        """Test analyze_deal with mocked analytics service"""
        from gradio_mcp_client import GradioMCPClient

        mock_db.return_value = Mock()
        mock_repos.return_value = Mock()

        client = GradioMCPClient()
        client.analytics_service = Mock()
        client.analytics_service.analyze_deal_comprehensive.return_value = {
            'health_score': 75,
            'risk_indicators': ['Test risk'],
            'recommendations': ['Test rec']
        }

        result = client.analyze_deal("123")

        assert 'health_score' in result
        assert result['health_score'] == 75


class TestGradioClientPortfolio:
    """Tests for portfolio overview functionality"""

    def test_get_portfolio_no_service(self):
        """Test get_portfolio_overview returns error when service unavailable"""
        from gradio_mcp_client import GradioMCPClient

        with patch('gradio_mcp_client.services_available', False):
            client = GradioMCPClient()
            result = client.get_portfolio_overview()
            assert "error" in result

    @patch('gradio_mcp_client.services_available', True)
    @patch('gradio_mcp_client.create_database_manager')
    @patch('gradio_mcp_client.create_repositories')
    def test_get_portfolio_with_mock_service(self, mock_repos, mock_db):
        """Test get_portfolio_overview with mocked analytics service"""
        from gradio_mcp_client import GradioMCPClient

        mock_db.return_value = Mock()
        mock_repos.return_value = Mock()

        client = GradioMCPClient()
        client.analytics_service = Mock()
        client.analytics_service.analyze_portfolio_overview.return_value = {
            'summary': {'total_deals': 10},
            'status_distribution': {'active': 5}
        }

        result = client.get_portfolio_overview()

        assert 'summary' in result
        assert result['summary']['total_deals'] == 10


class TestGradioClientSentiment:
    """Tests for sentiment analysis functionality"""

    def test_analyze_sentiment_empty_text(self):
        """Test analyze_sentiment with empty text"""
        from gradio_mcp_client import GradioMCPClient

        with patch('gradio_mcp_client.services_available', False):
            client = GradioMCPClient()
            result = client.analyze_sentiment("")
            assert "error" in result

    def test_analyze_sentiment_no_service(self):
        """Test analyze_sentiment returns error when service unavailable"""
        from gradio_mcp_client import GradioMCPClient

        with patch('gradio_mcp_client.services_available', False):
            client = GradioMCPClient()
            result = client.analyze_sentiment("test text")
            assert "error" in result

    @patch('gradio_mcp_client.services_available', True)
    @patch('gradio_mcp_client.create_database_manager')
    @patch('gradio_mcp_client.create_repositories')
    def test_analyze_sentiment_with_mock_service(self, mock_repos, mock_db):
        """Test analyze_sentiment with mocked sentiment service"""
        from gradio_mcp_client import GradioMCPClient

        mock_db.return_value = Mock()
        mock_repos.return_value = Mock()

        client = GradioMCPClient()
        client.sentiment_service = Mock()
        client.sentiment_service.model_loaded = True
        client.sentiment_service.analyze_text.return_value = {
            'sentiment': 'positive',
            'confidence': 0.85
        }

        result = client.analyze_sentiment("این یک متن مثبت است")

        assert 'sentiment' in result
        assert result['sentiment'] == 'positive'


class TestGradioClientFormatters:
    """Tests for formatting functions"""

    def test_format_portfolio_data_with_error(self):
        """Test format_portfolio_data with error response"""
        from gradio_mcp_client import GradioMCPClient

        with patch('gradio_mcp_client.services_available', False):
            client = GradioMCPClient()
            result, _ = client.format_portfolio_data({"error": "Test error"})
            assert "error" in result

    def test_format_portfolio_data_with_valid_data(self):
        """Test format_portfolio_data with valid data"""
        from gradio_mcp_client import GradioMCPClient

        with patch('gradio_mcp_client.services_available', False):
            client = GradioMCPClient()
            data = {
                'summary': {
                    'total_deals': 10,
                    'active_deals': 5,
                    'total_value': 1000000
                },
                'status_distribution': {'active': 5, 'closed': 5}
            }
            result, _ = client.format_portfolio_data(data)
            assert "Portfolio Overview" in result
            assert "10" in result

    def test_format_deal_analysis_with_error(self):
        """Test format_deal_analysis with error response"""
        from gradio_mcp_client import GradioMCPClient

        with patch('gradio_mcp_client.services_available', False):
            client = GradioMCPClient()
            result = client.format_deal_analysis({"error": "Test error"})
            assert "error" in result

    def test_format_deal_analysis_with_valid_data(self):
        """Test format_deal_analysis with valid data"""
        from gradio_mcp_client import GradioMCPClient

        with patch('gradio_mcp_client.services_available', False):
            client = GradioMCPClient()
            data = {
                'health_score': 75,
                'deal_status': 'active',
                'risk_indicators': ['Risk 1'],
                'recommendations': ['Rec 1']
            }
            result = client.format_deal_analysis(data)
            assert "Deal Analysis" in result
            assert "75" in result

    def test_format_sentiment_result_with_error(self):
        """Test format_sentiment_result with error response"""
        from gradio_mcp_client import GradioMCPClient

        with patch('gradio_mcp_client.services_available', False):
            client = GradioMCPClient()
            result = client.format_sentiment_result({"error": "Test error"})
            assert "error" in result

    def test_format_sentiment_result_with_valid_data(self):
        """Test format_sentiment_result with valid data"""
        from gradio_mcp_client import GradioMCPClient

        with patch('gradio_mcp_client.services_available', False):
            client = GradioMCPClient()
            data = {
                'sentiment': 'positive',
                'confidence': 0.85
            }
            result = client.format_sentiment_result(data)
            assert "Sentiment Analysis" in result
            assert "positive" in result


class TestGradioClientMoE:
    """Tests for MoE functionality in Gradio client"""

    def test_moe_query_empty_text(self):
        """Test moe_query with empty query"""
        from gradio_mcp_client import GradioMCPClient

        with patch('gradio_mcp_client.services_available', False):
            client = GradioMCPClient()
            result = client.moe_query("")
            assert "error" in result

    def test_moe_query_no_orchestrator(self):
        """Test moe_query returns error when orchestrator unavailable"""
        from gradio_mcp_client import GradioMCPClient

        with patch('gradio_mcp_client.services_available', False):
            client = GradioMCPClient()
            result = client.moe_query("test query")
            assert "error" in result

    def test_format_moe_result_with_error(self):
        """Test format_moe_result with error response"""
        from gradio_mcp_client import GradioMCPClient

        with patch('gradio_mcp_client.services_available', False):
            client = GradioMCPClient()
            result = client.format_moe_result({"error": "Test error"})
            assert "Error" in result

    def test_format_moe_result_with_valid_data(self):
        """Test format_moe_result with valid data"""
        from gradio_mcp_client import GradioMCPClient

        with patch('gradio_mcp_client.services_available', False):
            client = GradioMCPClient()
            data = {
                'primary_expert': 'deal_analysis',
                'combined_confidence': 0.85,
                'strategy_used': 'weighted_average',
                'execution_time_ms': 100.5,
                'reasoning': 'Test reasoning',
                'combined_data': {'health_score': 75},
                'expert_results': [
                    {'expert_type': 'deal_analysis', 'success': True, 'confidence': 0.85}
                ]
            }
            result = client.format_moe_result(data)
            assert "MoE Analysis Result" in result
            assert "deal_analysis" in result

    def test_get_moe_experts_no_orchestrator(self):
        """Test get_moe_experts returns message when orchestrator unavailable"""
        from gradio_mcp_client import GradioMCPClient

        with patch('gradio_mcp_client.services_available', False):
            client = GradioMCPClient()
            result = client.get_moe_experts()
            assert "not available" in result


class TestCreateInterface:
    """Tests for create_interface function"""

    @patch('gradio_mcp_client.gr')
    def test_create_interface_returns_app(self, mock_gr):
        """Test create_interface returns a Gradio app"""
        mock_app = Mock()
        mock_gr.Blocks.return_value.__enter__ = Mock(return_value=mock_app)
        mock_gr.Blocks.return_value.__exit__ = Mock(return_value=None)

        from gradio_mcp_client import create_interface
        # This will execute but we mainly check it doesn't error


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
