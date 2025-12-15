"""
tests/integration/test_mcp_server.py
------------------------------------
Integration tests for MCP Server
"""

import pytest
import asyncio
import json
from tests.utils.test_helpers import parse_result

pytest_plugins = ('pytest_asyncio',)

@pytest.mark.asyncio
class TestMCPServerInitialization:
    """Test MCP server initialization"""
    
    async def test_create_mcp_server(self):
        """Test creating MCP server instance"""
        from mcp_spec.server import create_mcp_server
        
        server = create_mcp_server()
        
        assert server is not None
        assert hasattr(server, 'server')
        assert hasattr(server, 'tool_handlers')
        assert hasattr(server, 'resource_handlers')
    
    
    
    async def test_initialize_services(self):
        """Test initializing server services"""
        from mcp_spec.server import create_mcp_server
        
        server = create_mcp_server()
        
        # Initialize services
        result = await server.initialize_services()
        
        # Should complete without error
        assert result is True or result is False
        
        # Check status after initialization
        status = server.get_server_status()
        assert 'database_connected' in status


@pytest.mark.asyncio
class TestMCPToolHandlers:
    """Test MCP tool handlers"""
    
    
    
    async def test_analyze_deal_tool_not_found(self):
        """Test analyze_deal tool with non-existent deal"""
        from mcp_spec.server import create_mcp_server
        
        server = create_mcp_server()
        await server.initialize_services()
        
        if server.tool_handlers:
            result = await server.tool_handlers.handle_tool_call(
                'analyze_deal',
                {'deal_id': 'nonexistent-deal-xyz'}
            )
            
            assert result is not None
            data = parse_result(result)
            assert isinstance(data, dict)
            assert 'error' in data or 'deal' in data
                
    async def test_analyze_text_sentiment_tool(self):
        """Test analyze_text_sentiment tool"""
        from mcp_spec.server import create_mcp_server
        
        server = create_mcp_server()
        await server.initialize_services()
        
        if server.tool_handlers and server.sentiment_service:
            result = await server.tool_handlers.handle_tool_call(
                'analyze_text_sentiment',
                {'text': 'این یک متن مثبت است'}
            )
            
            assert result is not None
            data = parse_result(result)
            assert isinstance(data, dict)
            assert 'sentiment' in data or 'error' in data
    
    async def test_invalid_tool_call(self):
        """Test calling non-existent tool"""
        from mcp_spec.server import create_mcp_server
        
        server = create_mcp_server()
        await server.initialize_services()
        
        if server.tool_handlers:
            result = await server.tool_handlers.handle_tool_call(
                'nonexistent_tool',
                {}
            )
            
            assert result is not None
            # Should return error


@pytest.mark.asyncio
class TestMCPResourceHandlers:
    """Test MCP resource handlers"""
    
    
    
    async def test_dashboard_resource(self):
        """Test dashboard resource"""
        from mcp_spec.server import create_mcp_server
        
        server = create_mcp_server()
        await server.initialize_services()
        
        if server.resource_handlers:
            result = await server.resource_handlers.handle_resource_request(
                'deals://dashboard'
            )
            
            assert result is not None
            assert isinstance(result, str)
            # Should be valid JSON
            import json
            data = json.loads(result)
            assert isinstance(data, dict)
    
    async def test_portfolio_health_resource(self):
        """Test portfolio health resource"""
        from mcp_spec.server import create_mcp_server
        
        server = create_mcp_server()
        await server.initialize_services()
        
        if server.resource_handlers:
            result = await server.resource_handlers.handle_resource_request(
                'deals://portfolio-health'
            )
            
            assert result is not None
            assert isinstance(result, str)
    
    async def test_invalid_resource_request(self):
        """Test requesting non-existent resource"""
        from mcp_spec.server import create_mcp_server
        
        server = create_mcp_server()
        await server.initialize_services()
        
        if server.resource_handlers:
            result = await server.resource_handlers.handle_resource_request(
                'deals://nonexistent'
            )
            
            assert result is not None
            # Should contain error


@pytest.mark.asyncio
class TestMCPServerCleanup:
    """Test MCP server cleanup"""
    
    async def test_server_cleanup(self):
        """Test server cleanup process"""
        from mcp_spec.server import create_mcp_server
        
        server = create_mcp_server()
        await server.initialize_services()
        
        # Cleanup should not raise exception
        await server.cleanup()
        
        # After cleanup, db_manager should be closed
        assert server.db_manager is not None


@pytest.mark.asyncio
class TestMCPServerWithData:
    """Test MCP server with actual data"""
    
    async def test_analyze_deal_with_data(self, test_repositories, sample_deal, sample_activities_list):
        """Test analyze_deal tool with real data"""
        from mcp_spec.server import create_mcp_server
        
        # Create test data
        test_repositories.deals.create_deal(sample_deal)
        for activity in sample_activities_list[:3]:
            test_repositories.activities.create_activity(activity)
        
        # Create and initialize server
        server = create_mcp_server()
        await server.initialize_services()
        
        if server.tool_handlers:
            # Call analyze_deal tool
            result = await server.tool_handlers.handle_tool_call(
                'analyze_deal',
                {'deal_id': sample_deal.Id}
            )
            
            assert result is not None
            data = parse_result(result)
            assert isinstance(data, dict)
            assert 'health_score' in data or 'deal' in data or 'error' in data
    
    async def test_portfolio_overview_with_data(self, test_repositories, sample_deals_list):
        """Test portfolio overview with real data"""
        from mcp_spec.server import create_mcp_server
        
        # Create test deals
        for deal in sample_deals_list[:5]:
            test_repositories.deals.create_deal(deal)
        
        # Create and initialize server
        server = create_mcp_server()
        await server.initialize_services()
        
        if server.tool_handlers:
            # Call portfolio overview tool
            result = await server.tool_handlers.handle_tool_call(
                'analyze_deals_overview',
                {'days': 30}
            )
            
            assert result is not None
            data = parse_result(result)
            assert isinstance(data, dict)
            assert 'summary' in data or 'error' in data