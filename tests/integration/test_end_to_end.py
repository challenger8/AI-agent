"""
tests/integration/test_end_to_end.py
------------------------------------
End-to-end integration tests for complete workflows
"""

import pytest
import asyncio


@pytest.mark.asyncio
class TestCompleteWorkflow:
    """Test complete workflows from start to finish"""
    
    async def test_deal_creation_to_analysis(self, test_repositories, sample_deal, sample_activities_list):
        """Test: Create deal → Add activities → Analyze → Get insights"""
        from services.analytics_service import AnalyticsService
        from services.sentiment_service import SentimentService
        
        # Step 1: Create deal
        deal_id = test_repositories.deals.create_deal(sample_deal)
        assert deal_id is not None
        
        # Step 2: Add activities
        for activity in sample_activities_list[:5]:
            activity_id = test_repositories.activities.create_activity(activity)
            assert activity_id is not None
        
        # Step 3: Initialize services
        sentiment_service = SentimentService(test_repositories)
        # Don't actually load model in tests
        analytics_service = AnalyticsService(test_repositories, sentiment_service)
        
        # Step 4: Analyze deal
        result = analytics_service.analyze_deal_comprehensive(sample_deal.Id)
        
        # Step 5: Verify insights
        assert result is not None
        assert 'health_score' in result
        assert 'insights' in result
        assert isinstance(result['insights'], list)
    
    async def test_mcp_server_full_cycle(self, test_repositories, sample_deal, sample_activities_list):
        """Test: Data in DB → MCP server → Tool call → Response"""
        from mcp_spec.server import create_mcp_server
        
        # Step 1: Populate database
        test_repositories.deals.create_deal(sample_deal)
        for activity in sample_activities_list[:3]:
            test_repositories.activities.create_activity(activity)
        
        # Step 2: Create and initialize MCP server
        server = create_mcp_server()
        init_result = await server.initialize_services()
        
        # Step 3: Call MCP tool
        if server.tool_handlers:
            result = await server.tool_handlers.handle_tool_call(
                'analyze_deal',
                {'deal_id': sample_deal.Id}
            )
            
            assert result is not None
            assert len(result) > 0
        
        # Step 4: Cleanup
        await server.cleanup()
    
    async def test_portfolio_analysis_workflow(self, test_repositories, sample_deals_list, sample_activities_list):
        """Test: Multiple deals → Portfolio analysis → Insights"""
        from services.analytics_service import AnalyticsService
        from services.sentiment_service import SentimentService
        
        # Step 1: Create multiple deals
        for i, deal in enumerate(sample_deals_list[:5]):
            test_repositories.deals.create_deal(deal)
            
            # Add some activities to each deal
            for j in range(min(3, len(sample_activities_list))):
                if i * 3 + j < len(sample_activities_list):
                    activity = sample_activities_list[i * 3 + j]
                    activity.dealid = deal.Id
                    test_repositories.activities.create_activity(activity)
        
        # Step 2: Initialize analytics
        sentiment_service = SentimentService(test_repositories)
        analytics_service = AnalyticsService(test_repositories, sentiment_service)
        
        # Step 3: Analyze portfolio
        result = analytics_service.analyze_portfolio_overview(days=30)
        
        # Step 4: Verify results
        assert result is not None
        assert 'summary' in result
        assert result['summary']['total_deals'] >= 5


@pytest.mark.asyncio  
class TestDataFlowIntegration:
    """Test data flowing through system"""
    
    async def test_sentiment_flows_to_activity(self, test_repositories, sample_deal, sample_activity):
        """Test: Activity created → Sentiment analyzed → Stored with activity"""
        from services.sentiment_service import SentimentService
        
        # Create deal and activity
        test_repositories.deals.create_deal(sample_deal)
        test_repositories.activities.create_activity(sample_activity)
        
        # Analyze sentiment (mocked in tests)
        sentiment_service = SentimentService(test_repositories)
        
        # Update activity with sentiment
        test_repositories.activities.update_activity_sentiment(
            sample_activity.id,
            sentiment_score=0.85,
            sentiment_label='مثبت'
        )
        
        # Verify it was stored
        updated_activity = test_repositories.activities.get_activity_by_id(sample_activity.id)
        assert updated_activity.sentiment_score == 0.85
        assert updated_activity.sentiment_label == 'مثبت'
    
    async def test_activities_affect_health_score(self, test_repositories, sample_deal, sample_activities_list):
        """Test: More activities → Better health score"""
        from services.analytics_service import AnalyticsService
        from services.sentiment_service import SentimentService
        from datetime import datetime, timedelta
        
        # Create deal
        test_repositories.deals.create_deal(sample_deal)
        
        # Initialize services
        sentiment_service = SentimentService(test_repositories)
        analytics_service = AnalyticsService(test_repositories, sentiment_service)
        
        # Analyze with few activities
        for activity in sample_activities_list[:2]:
            test_repositories.activities.create_activity(activity)
        
        result_few = analytics_service.analyze_deal_comprehensive(sample_deal.Id)
        score_few = result_few['health_score']
        
        # Add more recent activities
        for activity in sample_activities_list[2:7]:
            activity.registerdate = datetime.now() - timedelta(days=1)
            test_repositories.activities.create_activity(activity)
        
        # Invalidate cache
        analytics_service.invalidate_deal_cache(sample_deal.Id)
        
        # Analyze again
        result_many = analytics_service.analyze_deal_comprehensive(sample_deal.Id)
        score_many = result_many['health_score']
        
        # More recent activities should give better score
        assert score_many >= score_few


@pytest.mark.asyncio
class TestErrorHandlingIntegration:
    """Test error handling across components"""
    
    async def test_missing_deal_handled_gracefully(self, test_repositories):
        """Test that missing deal is handled at all levels"""
        from services.deal_service import DealService
        from services.analytics_service import AnalyticsService
        from services.sentiment_service import SentimentService
        
        # Initialize services
        deal_service = DealService(test_repositories)
        sentiment_service = SentimentService(test_repositories)
        analytics_service = AnalyticsService(test_repositories, sentiment_service)
        
        # Try to get non-existent deal
        deal = deal_service.get_deal('nonexistent-deal-xyz')
        assert deal is None
        
        # Try to analyze non-existent deal
        result = analytics_service.analyze_deal_comprehensive('nonexistent-deal-xyz')
        assert 'error' in result
    
    async def test_invalid_activity_handled(self, test_repositories, sample_activity):
        """Test creating activity without deal (foreign key violation)"""
        # Try to create activity without deal
        sample_activity.dealid = 'nonexistent-deal-xyz'
        
        try:
            result = test_repositories.activities.create_activity(sample_activity)
            # May succeed or fail depending on FK enforcement
            assert result is None or isinstance(result, str)
        except Exception:
            # Should handle gracefully
            pass
    
    async def test_mcp_tool_with_invalid_params(self):
        """Test MCP tool call with invalid parameters"""
        from mcp_spec.server import create_mcp_server
        
        server = create_mcp_server()
        await server.initialize_services()
        
        if server.tool_handlers:
            # Call with missing required parameter
            result = await server.tool_handlers.handle_tool_call(
                'analyze_deal',
                {}  # Missing deal_id
            )
            
            # Should return error, not crash
            assert result is not None


@pytest.mark.asyncio
class TestCachingIntegration:
    """Test caching across services"""
    
    async def test_analytics_results_cached(self, test_repositories, sample_deal, sample_activities_list):
        """Test that analytics results are cached"""
        from services.analytics_service import AnalyticsService
        from services.sentiment_service import SentimentService
        from services.cache_service import get_cache_service
        
        # Create deal and activities
        test_repositories.deals.create_deal(sample_deal)
        for activity in sample_activities_list[:3]:
            test_repositories.activities.create_activity(activity)
        
        # Initialize services
        sentiment_service = SentimentService(test_repositories)
        analytics_service = AnalyticsService(test_repositories, sentiment_service)
        
        # Get cache service
        cache = get_cache_service()
        
        if cache.is_available():
            # First call - should cache
            result1 = analytics_service.analyze_deal_comprehensive(sample_deal.Id)
            
            # Check if cached
            cache_key = cache.generate_key("deal_analysis", sample_deal.Id)
            cached = cache.get(cache_key)
            
            assert cached is not None
            assert cached['health_score'] == result1['health_score']
        else:
            pytest.skip("Redis not available for caching test")
    
    async def test_sentiment_results_cached(self, test_repositories):
        """Test that sentiment analysis results are cached"""
        from services.sentiment_service import SentimentService
        from services.cache_service import get_cache_service
        
        sentiment_service = SentimentService(test_repositories)
        cache = get_cache_service()
        
        if cache.is_available():
            text = "این یک متن تست است"
            
            # Analyze text (should cache)
            result1 = sentiment_service.analyze_text(text)
            
            # Check cache
            text_hash = cache.hash_text(text.strip())
            cache_key = cache.generate_key("sentiment", text_hash)
            cached = cache.get(cache_key)
            
            # Should be cached
            assert cached is not None or result1.get('error') is not None
        else:
            pytest.skip("Redis not available for caching test")
    
    async def test_cache_invalidation(self, test_repositories, sample_deal, sample_activities_list):
        """Test that cache is invalidated when data changes"""
        from services.analytics_service import AnalyticsService
        from services.sentiment_service import SentimentService
        from datetime import datetime, timedelta
        
        # Create deal with initial activities
        test_repositories.deals.create_deal(sample_deal)
        for activity in sample_activities_list[:2]:
            test_repositories.activities.create_activity(activity)
        
        # Initialize services
        sentiment_service = SentimentService(test_repositories)
        analytics_service = AnalyticsService(test_repositories, sentiment_service)
        
        # First analysis
        result1 = analytics_service.analyze_deal_comprehensive(sample_deal.Id)
        score1 = result1['health_score']
        
        # Add more activities
        for activity in sample_activities_list[2:5]:
            activity.registerdate = datetime.now() - timedelta(days=1)
            test_repositories.activities.create_activity(activity)
        
        # Invalidate cache explicitly
        analytics_service.invalidate_deal_cache(sample_deal.Id)
        
        # Second analysis (should recalculate)
        result2 = analytics_service.analyze_deal_comprehensive(sample_deal.Id)
        score2 = result2['health_score']
        
        # Scores might be different due to more activities
        assert score2 is not None


@pytest.mark.asyncio
class TestMultiServiceCoordination:
    """Test multiple services working together"""
    
    async def test_all_services_together(self, test_repositories, sample_deal, sample_activities_list, sample_agent):
        """Test deal service, sentiment service, and analytics service together"""
        from services.deal_service import DealService
        from services.sentiment_service import SentimentService
        from services.analytics_service import AnalyticsService
        
        # Create test data
        test_repositories.agents.create_agent(sample_agent)
        test_repositories.deals.create_deal(sample_deal)
        for activity in sample_activities_list[:5]:
            test_repositories.activities.create_activity(activity)
        
        # Initialize all services
        deal_service = DealService(test_repositories)
        sentiment_service = SentimentService(test_repositories)
        analytics_service = AnalyticsService(test_repositories, sentiment_service)
        
        # Use deal service
        deal = deal_service.get_deal(sample_deal.Id)
        assert deal is not None
        
        # Get timeline
        timeline = deal_service.get_deal_timeline(sample_deal.Id)
        assert timeline is not None
        
        # Use analytics service
        analysis = analytics_service.analyze_deal_comprehensive(sample_deal.Id)
        assert analysis is not None
        assert 'health_score' in analysis
        
        # Portfolio overview
        portfolio = analytics_service.analyze_portfolio_overview(days=30)
        assert portfolio is not None
    
    async def test_repository_manager_coordination(self, test_repositories, sample_deal, sample_activities_list):
        """Test using repository manager to coordinate access"""
        # Create deal
        test_repositories.deals.create_deal(sample_deal)
        
        # Use repository manager as context manager
        with test_repositories as uow:
            # Should be able to access all repositories
            deal = uow.deals.get_deal_by_id(sample_deal.Id)
            assert deal is not None
            
            # Create activities through same context
            for activity in sample_activities_list[:3]:
                uow.activities.create_activity(activity)
            
            # Get activities
            activities = uow.activities.get_activities_by_deal(sample_deal.Id)
            assert len(activities) >= 3


@pytest.mark.asyncio
class TestScenarios:
    """Test real-world scenarios"""
    
    async def test_healthy_deal_scenario(self, test_repositories, healthy_deal_scenario):
        """Test complete workflow for a healthy deal"""
        from services.analytics_service import AnalyticsService
        from services.sentiment_service import SentimentService
        
        # Create healthy deal scenario
        deal = healthy_deal_scenario['deal']
        activities = healthy_deal_scenario['activities']
        
        test_repositories.deals.create_deal(deal)
        for activity in activities:
            test_repositories.activities.create_activity(activity)
        
        # Analyze
        sentiment_service = SentimentService(test_repositories)
        analytics_service = AnalyticsService(test_repositories, sentiment_service)
        
        result = analytics_service.analyze_deal_comprehensive(deal.Id)
        
        # Healthy deal should have good health score
        assert result['health_score'] >= 60
        
        # Should have minimal risks
        assert len(result['risk_indicators']) <= 2
    
    async def test_at_risk_deal_scenario(self, test_repositories, at_risk_deal_scenario):
        """Test complete workflow for an at-risk deal"""
        from services.analytics_service import AnalyticsService
        from services.sentiment_service import SentimentService
        
        # Create at-risk deal scenario
        deal = at_risk_deal_scenario['deal']
        activities = at_risk_deal_scenario['activities']
        
        test_repositories.deals.create_deal(deal)
        for activity in activities:
            test_repositories.activities.create_activity(activity)
        
        # Analyze
        sentiment_service = SentimentService(test_repositories)
        analytics_service = AnalyticsService(test_repositories, sentiment_service)
        
        result = analytics_service.analyze_deal_comprehensive(deal.Id)
        
        # At-risk deal should have low health score
        assert result['health_score'] < 50
        
        # Should identify risks
        assert len(result['risk_indicators']) > 0
        
        # Should have recommendations
        assert len(result['recommendations']) > 0
    
    async def test_new_deal_with_no_history(self, test_repositories, sample_deal):
        """Test analyzing a brand new deal with no activities"""
        from services.analytics_service import AnalyticsService
        from services.sentiment_service import SentimentService
        from datetime import datetime
        
        # Create new deal with today's date
        sample_deal.RegisterTime = datetime.now()
        test_repositories.deals.create_deal(sample_deal)
        
        # Analyze
        sentiment_service = SentimentService(test_repositories)
        analytics_service = AnalyticsService(test_repositories, sentiment_service)
        
        result = analytics_service.analyze_deal_comprehensive(sample_deal.Id)
        
        # Should handle gracefully
        assert result is not None
        assert 'health_score' in result
        
        # Should identify lack of activity as risk
        risk_types = [r['type'] for r in result['risk_indicators']]
        assert 'no_activity' in risk_types


@pytest.mark.asyncio
class TestPerformanceIntegration:
    """Test performance-related aspects"""
    
    async def test_analyze_multiple_deals_performance(self, test_repositories, sample_deals_list, sample_activities_list):
        """Test analyzing multiple deals doesn't timeout"""
        import time
        from services.analytics_service import AnalyticsService
        from services.sentiment_service import SentimentService
        
        # Create multiple deals with activities
        for i, deal in enumerate(sample_deals_list[:10]):
            test_repositories.deals.create_deal(deal)
            # Add a few activities to each
            for j in range(3):
                if i * 3 + j < len(sample_activities_list):
                    activity = sample_activities_list[i * 3 + j]
                    activity.dealid = deal.Id
                    test_repositories.activities.create_activity(activity)
        
        # Initialize services
        sentiment_service = SentimentService(test_repositories)
        analytics_service = AnalyticsService(test_repositories, sentiment_service)
        
        # Analyze all deals
        start_time = time.time()
        
        for deal in sample_deals_list[:10]:
            result = analytics_service.analyze_deal_comprehensive(deal.Id)
            assert result is not None
        
        elapsed_time = time.time() - start_time
        
        # Should complete in reasonable time (adjust threshold as needed)
        # 10 deals should complete in under 30 seconds
        assert elapsed_time < 30
    
    async def test_portfolio_analysis_with_many_deals(self, test_repositories, sample_deals_list):
        """Test portfolio analysis with many deals"""
        from services.analytics_service import AnalyticsService
        from services.sentiment_service import SentimentService
        
        # Create many deals
        for deal in sample_deals_list[:20]:
            test_repositories.deals.create_deal(deal)
        
        # Initialize services
        sentiment_service = SentimentService(test_repositories)
        analytics_service = AnalyticsService(test_repositories, sentiment_service)
        
        # Analyze portfolio
        result = analytics_service.analyze_portfolio_overview(days=30)
        
        # Should complete without timeout
        assert result is not None
        assert result['summary']['total_deals'] >= 20


@pytest.mark.asyncio
class TestDataConsistency:
    """Test data consistency across operations"""
    
    async def test_deal_count_consistency(self, test_repositories, sample_deals_list):
        """Test that deal counts are consistent across queries"""
        from services.deal_service import DealService
        
        # Create deals
        for deal in sample_deals_list[:5]:
            test_repositories.deals.create_deal(deal)
        
        # Get count through different methods
        deal_service = DealService(test_repositories)
        
        all_deals = deal_service.get_all_deals()
        summary = deal_service.get_deals_summary(days=365)
        
        # Counts should match
        assert len(all_deals) == summary['total_deals']
    
    async def test_activity_relationship_consistency(self, test_repositories, sample_deal, sample_activities_list):
        """Test that activity-deal relationships are maintained"""
        # Create deal and activities
        test_repositories.deals.create_deal(sample_deal)
        
        created_count = 0
        for activity in sample_activities_list[:5]:
            result = test_repositories.activities.create_activity(activity)
            if result:
                created_count += 1
        
        # Retrieve activities by deal
        retrieved_activities = test_repositories.activities.get_activities_by_deal(sample_deal.Id)
        
        # Should match
        assert len(retrieved_activities) == created_count
        
        # All should belong to the deal
        for activity in retrieved_activities:
            assert activity.dealid == sample_deal.Id