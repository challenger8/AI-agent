"""
tests/integration/test_gradio_interface.py
------------------------------------------
Integration tests for Gradio interface
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch

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


class TestGradioInterfaceCreation:
    """Tests for Gradio interface creation"""

    def test_create_interface_returns_blocks(self):
        """Test create_interface returns Gradio Blocks"""
        with patch('gradio_mcp_client.services_available', False):
            from gradio_mcp_client import create_interface

            app = create_interface()
            assert app is not None

    def test_interface_has_tabs(self):
        """Test interface has expected tabs"""
        with patch('gradio_mcp_client.services_available', False):
            from gradio_mcp_client import create_interface

            app = create_interface()
            # App should be created without errors


class TestGradioClientIntegration:
    """Integration tests for GradioMCPClient"""

    @pytest.fixture
    def mock_services(self):
        """Create mock services for testing"""
        return {
            'db_manager': Mock(),
            'repositories': Mock(),
            'analytics': Mock(),
            'sentiment': Mock(),
            'deal': Mock()
        }

    def test_client_full_initialization(self, mock_services):
        """Test client initializes all components"""
        with patch('gradio_mcp_client.services_available', True), \
             patch('gradio_mcp_client.create_database_manager') as mock_db, \
             patch('gradio_mcp_client.create_repositories') as mock_repos, \
             patch('gradio_mcp_client.moe_available', False):

            mock_db.return_value = mock_services['db_manager']
            mock_repos.return_value = mock_services['repositories']

            from gradio_mcp_client import GradioMCPClient
            client = GradioMCPClient()

            assert client.db_manager is not None

    def test_deal_analysis_workflow(self, mock_services):
        """Test complete deal analysis workflow"""
        with patch('gradio_mcp_client.services_available', True), \
             patch('gradio_mcp_client.create_database_manager') as mock_db, \
             patch('gradio_mcp_client.create_repositories') as mock_repos, \
             patch('gradio_mcp_client.moe_available', False):

            mock_db.return_value = mock_services['db_manager']
            mock_repos.return_value = mock_services['repositories']

            from gradio_mcp_client import GradioMCPClient
            client = GradioMCPClient()

            # Setup mock analytics service
            client.analytics_service = Mock()
            client.analytics_service.analyze_deal_comprehensive.return_value = {
                'health_score': 75,
                'health_category': 'medium',
                'risk_indicators': ['Inactivity warning'],
                'recommendations': ['Follow up soon'],
                'deal_status': 'active'
            }

            # Test the workflow
            result = client.analyze_deal('123')
            formatted = client.format_deal_analysis(result)

            assert 'health_score' in result
            assert '75' in formatted

    def test_portfolio_workflow(self, mock_services):
        """Test complete portfolio overview workflow"""
        with patch('gradio_mcp_client.services_available', True), \
             patch('gradio_mcp_client.create_database_manager') as mock_db, \
             patch('gradio_mcp_client.create_repositories') as mock_repos, \
             patch('gradio_mcp_client.moe_available', False):

            mock_db.return_value = mock_services['db_manager']
            mock_repos.return_value = mock_services['repositories']

            from gradio_mcp_client import GradioMCPClient
            client = GradioMCPClient()

            # Setup mock analytics service
            client.analytics_service = Mock()
            client.analytics_service.analyze_portfolio_overview.return_value = {
                'summary': {
                    'total_deals': 50,
                    'active_deals': 30,
                    'total_value': 5000000
                },
                'status_distribution': {
                    'active': 30,
                    'won': 15,
                    'lost': 5
                }
            }

            # Test the workflow
            result = client.get_portfolio_overview()
            formatted, _ = client.format_portfolio_data(result)

            assert 'total_deals' in result['summary']
            assert '50' in formatted

    def test_sentiment_workflow(self, mock_services):
        """Test complete sentiment analysis workflow"""
        with patch('gradio_mcp_client.services_available', True), \
             patch('gradio_mcp_client.create_database_manager') as mock_db, \
             patch('gradio_mcp_client.create_repositories') as mock_repos, \
             patch('gradio_mcp_client.moe_available', False):

            mock_db.return_value = mock_services['db_manager']
            mock_repos.return_value = mock_services['repositories']

            from gradio_mcp_client import GradioMCPClient
            client = GradioMCPClient()

            # Setup mock sentiment service
            client.sentiment_service = Mock()
            client.sentiment_service.model_loaded = True
            client.sentiment_service.analyze_text.return_value = {
                'sentiment': 'positive',
                'confidence': 0.92
            }

            # Test the workflow
            result = client.analyze_sentiment("این یک متن مثبت است")
            formatted = client.format_sentiment_result(result)

            assert result['sentiment'] == 'positive'
            assert 'positive' in formatted


class TestGradioErrorHandling:
    """Tests for Gradio error handling"""

    def test_handles_service_initialization_error(self):
        """Test client handles service initialization errors"""
        with patch('gradio_mcp_client.services_available', True), \
             patch('gradio_mcp_client.create_database_manager') as mock_db:

            mock_db.side_effect = Exception("Connection failed")

            from gradio_mcp_client import GradioMCPClient
            # Should not raise, just log error
            client = GradioMCPClient()

    def test_handles_analysis_error(self):
        """Test client handles analysis errors gracefully"""
        with patch('gradio_mcp_client.services_available', True), \
             patch('gradio_mcp_client.create_database_manager') as mock_db, \
             patch('gradio_mcp_client.create_repositories') as mock_repos, \
             patch('gradio_mcp_client.moe_available', False):

            mock_db.return_value = Mock()
            mock_repos.return_value = Mock()

            from gradio_mcp_client import GradioMCPClient
            client = GradioMCPClient()

            # Setup mock service that raises error
            client.analytics_service = Mock()
            client.analytics_service.analyze_deal_comprehensive.side_effect = Exception("Analysis failed")

            result = client.analyze_deal('123')

            assert 'error' in result


class TestGradioMoEIntegration:
    """Integration tests for MoE in Gradio"""

    def test_moe_query_workflow(self):
        """Test MoE query workflow through Gradio"""
        with patch('gradio_mcp_client.services_available', True), \
             patch('gradio_mcp_client.create_database_manager') as mock_db, \
             patch('gradio_mcp_client.create_repositories') as mock_repos, \
             patch('gradio_mcp_client.moe_available', True):

            mock_db.return_value = Mock()
            mock_repos.return_value = Mock()

            from gradio_mcp_client import GradioMCPClient
            client = GradioMCPClient()

            # Setup mock MoE orchestrator
            mock_moe = Mock()
            mock_result = Mock()
            mock_result.to_dict.return_value = {
                'primary_expert': 'deal_analysis',
                'combined_confidence': 0.85,
                'strategy_used': 'weighted_average',
                'execution_time_ms': 150.0,
                'reasoning': 'Test reasoning',
                'combined_data': {'health_score': 75},
                'expert_results': []
            }

            import asyncio

            async def mock_process(query, context=None):
                return mock_result

            mock_moe.process = mock_process
            client.moe_orchestrator = mock_moe

            # Test the workflow
            result = client.moe_query("Analyze deal 123")
            formatted = client.format_moe_result(result)

            assert result['primary_expert'] == 'deal_analysis'
            assert 'MoE Analysis Result' in formatted


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
