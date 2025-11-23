"""
tests/integration/test_gradio_moe.py
------------------------------------
Integration tests for MoE functionality in Gradio interface
"""

import pytest
import asyncio
import sys
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

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


class TestGradioMoEIntegration:
    """Integration tests for MoE in Gradio client"""

    @pytest.fixture
    def mock_moe_result(self):
        """Create a mock MoE result"""
        return {
            'query': 'Analyze deal 123',
            'primary_expert': 'deal_analysis',
            'combined_confidence': 0.85,
            'strategy_used': 'weighted_average',
            'execution_time_ms': 150.0,
            'reasoning': 'Combined 2 expert results',
            'combined_data': {
                'health_score': 75,
                'risk_indicators': ['Inactivity warning'],
                'recommendations': ['Schedule follow-up']
            },
            'expert_results': [
                {
                    'expert_type': 'deal_analysis',
                    'success': True,
                    'confidence': 0.85,
                    'data': {'health_score': 75}
                },
                {
                    'expert_type': 'risk_assessment',
                    'success': True,
                    'confidence': 0.78,
                    'data': {'risk_level': 'medium'}
                }
            ],
            'metadata': {
                'routing': {
                    'selected_experts': ['deal_analysis', 'risk_assessment']
                }
            }
        }

    def test_moe_query_formatting(self, mock_moe_result):
        """Test MoE result formatting"""
        with patch('gradio_mcp_client.services_available', False):
            from gradio_mcp_client import GradioMCPClient
            client = GradioMCPClient()

            formatted = client.format_moe_result(mock_moe_result)

            assert 'MoE Analysis Result' in formatted
            assert 'deal_analysis' in formatted
            assert '85' in formatted  # confidence

    def test_moe_query_with_different_experts(self):
        """Test MoE queries routed to different experts"""
        with patch('gradio_mcp_client.services_available', False):
            from gradio_mcp_client import GradioMCPClient
            client = GradioMCPClient()

            # Test different result types
            sentiment_result = {
                'primary_expert': 'sentiment',
                'combined_confidence': 0.9,
                'strategy_used': 'winner_take_all',
                'execution_time_ms': 200.0,
                'reasoning': 'Sentiment analysis completed',
                'combined_data': {
                    'sentiment': 'positive',
                    'confidence': 0.9
                },
                'expert_results': []
            }

            formatted = client.format_moe_result(sentiment_result)
            assert 'sentiment' in formatted

    def test_moe_error_handling(self):
        """Test MoE error handling in Gradio"""
        with patch('gradio_mcp_client.services_available', False):
            from gradio_mcp_client import GradioMCPClient
            client = GradioMCPClient()

            error_result = {'error': 'Expert execution failed'}
            formatted = client.format_moe_result(error_result)

            assert 'Error' in formatted

    def test_moe_empty_query(self):
        """Test MoE with empty query"""
        with patch('gradio_mcp_client.services_available', False):
            from gradio_mcp_client import GradioMCPClient
            client = GradioMCPClient()

            result = client.moe_query("")
            assert 'error' in result

    def test_moe_get_experts_display(self):
        """Test getting expert descriptions for display"""
        with patch('gradio_mcp_client.services_available', True), \
             patch('gradio_mcp_client.create_database_manager') as mock_db, \
             patch('gradio_mcp_client.create_repositories') as mock_repos, \
             patch('gradio_mcp_client.moe_available', True):

            mock_db.return_value = Mock()
            mock_repos.return_value = Mock()

            from gradio_mcp_client import GradioMCPClient
            from services.moe.moe_orchestrator import MoEOrchestrator

            client = GradioMCPClient()
            client.moe_orchestrator = MoEOrchestrator()

            result = client.get_moe_experts()

            assert 'Available Experts' in result
            assert 'deal_analysis' in result


class TestMoEWorkflows:
    """Test complete MoE workflows through Gradio"""

    @pytest.fixture
    def setup_client(self):
        """Setup client with mock MoE orchestrator"""
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

            def create_result(data):
                result = Mock()
                result.to_dict.return_value = data
                return result

            async def mock_process(query, context=None):
                return create_result({
                    'primary_expert': 'deal_analysis',
                    'combined_confidence': 0.85,
                    'strategy_used': 'weighted_average',
                    'execution_time_ms': 100.0,
                    'reasoning': f'Processed: {query}',
                    'combined_data': {'result': 'success'},
                    'expert_results': []
                })

            mock_moe.process = mock_process
            mock_moe.get_expert_descriptions.return_value = {
                'deal_analysis': 'Analyzes deals',
                'sentiment': 'Analyzes sentiment'
            }

            client.moe_orchestrator = mock_moe

            return client

    def test_deal_analysis_moe_workflow(self, setup_client):
        """Test deal analysis through MoE"""
        client = setup_client

        result = client.moe_query("Analyze deal 123")
        formatted = client.format_moe_result(result)

        assert result['primary_expert'] == 'deal_analysis'
        assert 'MoE Analysis Result' in formatted

    def test_sentiment_moe_workflow(self, setup_client):
        """Test sentiment analysis through MoE"""
        client = setup_client

        result = client.moe_query("What's the sentiment of this text?")

        assert 'combined_confidence' in result

    def test_search_moe_workflow(self, setup_client):
        """Test search through MoE"""
        client = setup_client

        result = client.moe_query("Find deals related to software")

        assert 'execution_time_ms' in result


class TestMoEResultFormatting:
    """Test MoE result formatting in detail"""

    @pytest.fixture
    def client(self):
        """Create client instance"""
        with patch('gradio_mcp_client.services_available', False):
            from gradio_mcp_client import GradioMCPClient
            return GradioMCPClient()

    def test_format_with_health_score(self, client):
        """Test formatting result with health score"""
        result = {
            'primary_expert': 'deal_analysis',
            'combined_confidence': 0.85,
            'strategy_used': 'weighted_average',
            'execution_time_ms': 100.0,
            'reasoning': 'Test',
            'combined_data': {'health_score': 75},
            'expert_results': []
        }

        formatted = client.format_moe_result(result)
        assert 'Health Score: 75' in formatted

    def test_format_with_sentiment(self, client):
        """Test formatting result with sentiment"""
        result = {
            'primary_expert': 'sentiment',
            'combined_confidence': 0.9,
            'strategy_used': 'winner_take_all',
            'execution_time_ms': 50.0,
            'reasoning': 'Test',
            'combined_data': {'sentiment': 'positive'},
            'expert_results': []
        }

        formatted = client.format_moe_result(result)
        assert 'Sentiment: positive' in formatted

    def test_format_with_risk_indicators(self, client):
        """Test formatting result with risk indicators"""
        result = {
            'primary_expert': 'risk_assessment',
            'combined_confidence': 0.75,
            'strategy_used': 'hierarchical',
            'execution_time_ms': 120.0,
            'reasoning': 'Test',
            'combined_data': {
                'risk_indicators': ['Risk 1', 'Risk 2']
            },
            'expert_results': []
        }

        formatted = client.format_moe_result(result)
        assert 'Risk Indicators' in formatted
        assert 'Risk 1' in formatted

    def test_format_with_recommendations(self, client):
        """Test formatting result with recommendations"""
        result = {
            'primary_expert': 'deal_analysis',
            'combined_confidence': 0.8,
            'strategy_used': 'weighted_average',
            'execution_time_ms': 80.0,
            'reasoning': 'Test',
            'combined_data': {
                'recommendations': ['Action 1', 'Action 2']
            },
            'expert_results': []
        }

        formatted = client.format_moe_result(result)
        assert 'Recommendations' in formatted
        assert 'Action 1' in formatted

    def test_format_with_search_results(self, client):
        """Test formatting result with search results count"""
        result = {
            'primary_expert': 'search',
            'combined_confidence': 0.7,
            'strategy_used': 'winner_take_all',
            'execution_time_ms': 200.0,
            'reasoning': 'Test',
            'combined_data': {'total_results': 15},
            'expert_results': []
        }

        formatted = client.format_moe_result(result)
        assert 'Search Results: 15' in formatted

    def test_format_with_expert_contributions(self, client):
        """Test formatting with expert contributions"""
        result = {
            'primary_expert': 'deal_analysis',
            'combined_confidence': 0.85,
            'strategy_used': 'weighted_average',
            'execution_time_ms': 150.0,
            'reasoning': 'Test',
            'combined_data': {},
            'expert_results': [
                {'expert_type': 'deal_analysis', 'success': True, 'confidence': 0.85},
                {'expert_type': 'risk_assessment', 'success': True, 'confidence': 0.78}
            ]
        }

        formatted = client.format_moe_result(result)
        assert 'Expert Contributions' in formatted
        assert 'deal_analysis: Success' in formatted


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
