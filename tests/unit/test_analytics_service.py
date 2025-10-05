"""
tests/unit/test_analytics_service.py
------------------------------------
Unit tests for AnalyticsService (MOST IMPORTANT!)
"""

import pytest
from datetime import datetime, timedelta


class TestAnalyticsServiceBasic:
    """Test basic AnalyticsService functionality"""
    
    def test_service_initialization(self, analytics_service):
        """Test analytics service creates successfully"""
        assert analytics_service is not None
        assert hasattr(analytics_service, 'deal_service')
        assert hasattr(analytics_service, 'sentiment_service')
    
    def test_analyze_deal_comprehensive_not_found(self, analytics_service):
        """Test analyzing non-existent deal"""
        result = analytics_service.analyze_deal_comprehensive('nonexistent-deal')
        
        assert result is not None
        assert 'error' in result


class TestHealthScoreCalculation:
    """Test health score calculation logic (CRITICAL)"""
    
    def test_calculate_health_score_basic(self, analytics_service, sample_deal, sample_activities_list):
        """Test basic health score calculation"""
        sentiment_summary = {
            'total_activities': len(sample_activities_list),
            'dominant_sentiment': 'مثبت',
            'sentiment_available': True
        }
        
        score = analytics_service._calculate_health_score(
            sample_deal.to_dict(),
            sample_activities_list[:5],
            sentiment_summary
        )
        
        assert score is not None
        assert isinstance(score, int)
        assert 0 <= score <= 100
    
    def test_health_score_no_activities(self, analytics_service, sample_deal):
        """Test health score with no activities (should be low)"""
        sentiment_summary = {'sentiment_available': False}
        
        score = analytics_service._calculate_health_score(
            sample_deal.to_dict(),
            [],
            sentiment_summary
        )
        
        assert score is not None
        assert score < 50  # Should be penalized for no activities
    
    def test_health_score_recent_activity_bonus(self, analytics_service, sample_deal, sample_activities_list):
        """Test that recent activities increase health score"""
        # Make activities very recent
        for activity in sample_activities_list[:3]:
            activity.registerdate = datetime.now() - timedelta(days=2)
        
        sentiment_summary = {'sentiment_available': False}
        
        score = analytics_service._calculate_health_score(
            sample_deal.to_dict(),
            sample_activities_list[:3],
            sentiment_summary
        )
        
        assert score >= 50  # Should have recent activity bonus
    
    def test_health_score_old_activity_penalty(self, analytics_service, sample_deal, sample_activities_list):
        """Test that old activities decrease health score"""
        # Make activities very old
        for activity in sample_activities_list[:3]:
            activity.registerdate = datetime.now() - timedelta(days=40)
        
        sentiment_summary = {'sentiment_available': False}
        
        score = analytics_service._calculate_health_score(
            sample_deal.to_dict(),
            sample_activities_list[:3],
            sentiment_summary
        )
        
        # Should be penalized for stale activity
        assert score < 60
    
    def test_health_score_positive_sentiment_bonus(self, analytics_service, sample_deal, sample_activities_list):
        """Test that positive sentiment increases score"""
        sentiment_summary = {
            'dominant_sentiment': 'مثبت',
            'sentiment_available': True
        }
        
        score_positive = analytics_service._calculate_health_score(
            sample_deal.to_dict(),
            sample_activities_list[:3],
            sentiment_summary
        )
        
        # Now test with negative sentiment
        sentiment_summary['dominant_sentiment'] = 'منفی'
        
        score_negative = analytics_service._calculate_health_score(
            sample_deal.to_dict(),
            sample_activities_list[:3],
            sentiment_summary
        )
        
        # Positive should be higher than negative
        assert score_positive > score_negative
    
    def test_health_score_many_activities_bonus(self, analytics_service, sample_deal, sample_activities_list):
        """Test that many activities increase score"""
        sentiment_summary = {'sentiment_available': False}
        
        # Test with few activities
        score_few = analytics_service._calculate_health_score(
            sample_deal.to_dict(),
            sample_activities_list[:2],
            sentiment_summary
        )
        
        # Test with many activities
        score_many = analytics_service._calculate_health_score(
            sample_deal.to_dict(),
            sample_activities_list,
            sentiment_summary
        )
        
        # More activities should give higher score
        assert score_many >= score_few
    
    def test_health_score_capped_at_100(self, analytics_service, sample_deal, sample_activities_list):
        """Test that health score never exceeds 100"""
        # Create ideal conditions
        for activity in sample_activities_list:
            activity.registerdate = datetime.now() - timedelta(days=1)
        
        sentiment_summary = {
            'dominant_sentiment': 'مثبت',
            'sentiment_available': True
        }
        
        score = analytics_service._calculate_health_score(
            sample_deal.to_dict(),
            sample_activities_list,
            sentiment_summary
        )
        
        assert score <= 100
    
    def test_health_score_minimum_zero(self, analytics_service, sample_deal):
        """Test that health score never goes below 0"""
        # Create worst conditions
        sample_deal.RegisterTime = datetime.now() - timedelta(days=200)
        
        sentiment_summary = {
            'dominant_sentiment': 'منفی',
            'sentiment_available': True
        }
        
        score = analytics_service._calculate_health_score(
            sample_deal.to_dict(),
            [],
            sentiment_summary
        )
        
        assert score >= 0


class TestRiskIdentification:
    """Test risk indicator identification"""
    
    def test_identify_risks_healthy_deal(self, analytics_service, healthy_deal_scenario):
        """Test that healthy deal has few/no risks"""
        risks = analytics_service._identify_risk_indicators(
            healthy_deal_scenario['deal'].to_dict(),
            healthy_deal_scenario['activities'],
            health_score=80
        )
        
        assert isinstance(risks, list)
        # Healthy deal should have minimal risks
        assert len(risks) <= 2
    
    def test_identify_risks_at_risk_deal(self, analytics_service, at_risk_deal_scenario):
        """Test that at-risk deal has multiple risks identified"""
        risks = analytics_service._identify_risk_indicators(
            at_risk_deal_scenario['deal'].to_dict(),
            at_risk_deal_scenario['activities'],
            health_score=30
        )
        
        assert isinstance(risks, list)
        assert len(risks) > 0
        
        # Check for expected risk types
        risk_types = [r['type'] for r in risks]
        assert 'low_health_score' in risk_types or 'stale_activity' in risk_types
    
    def test_identify_risk_no_activity(self, analytics_service, sample_deal):
        """Test risk identification for deal with no activities"""
        risks = analytics_service._identify_risk_indicators(
            sample_deal.to_dict(),
            [],
            health_score=30
        )
        
        assert len(risks) > 0
        risk_types = [r['type'] for r in risks]
        assert 'no_activity' in risk_types
    
    def test_identify_risk_stale_activity(self, analytics_service, sample_deal, sample_activities_list):
        """Test identification of stale activity risk"""
        # Make activities old
        for activity in sample_activities_list[:2]:
            activity.registerdate = datetime.now() - timedelta(days=20)
        
        risks = analytics_service._identify_risk_indicators(
            sample_deal.to_dict(),
            sample_activities_list[:2],
            health_score=50
        )
        
        risk_types = [r['type'] for r in risks]
        # Should identify stale activity
        assert 'stale_activity' in risk_types or len(risks) > 0


class TestPortfolioOverview:
    """Test portfolio-wide analytics"""
    
    def test_analyze_portfolio_overview_empty(self, analytics_service):
        """Test portfolio overview with no deals"""
        result = analytics_service.analyze_portfolio_overview(days=30)
        
        assert result is not None
        # Should handle empty portfolio gracefully
        assert 'summary' in result or 'message' in result
    
    def test_analyze_portfolio_overview_basic(self, analytics_service, test_repositories, sample_deals_list):
        """Test basic portfolio overview"""
        # Create some deals
        for deal in sample_deals_list[:3]:
            test_repositories.deals.create_deal(deal)
        
        result = analytics_service.analyze_portfolio_overview(days=30)
        
        assert result is not None
        assert 'summary' in result
        assert 'period_days' in result
        assert result['period_days'] == 30
    
    def test_analyze_portfolio_with_status_filter(self, analytics_service, test_repositories, sample_deals_list):
        """Test portfolio overview with status filter"""
        # Create deals
        for deal in sample_deals_list[:5]:
            test_repositories.deals.create_deal(deal)
        
        result = analytics_service.analyze_portfolio_overview(
            status='در حال پیگیری',
            days=30
        )
        
        assert result is not None
        assert result['status_filter'] == 'در حال پیگیری'


class TestAnalyticsHelperMethods:
    """Test helper methods in analytics service"""
    
    def test_create_activity_timeline(self, analytics_service, sample_activities_list):
        """Test activity timeline creation"""
        timeline = analytics_service._create_activity_timeline(
            sample_activities_list[:5]
        )
        
        assert isinstance(timeline, list)
        assert len(timeline) <= 20  # Should limit to last 20
        
        if len(timeline) > 0:
            # Check timeline structure
            assert 'date' in timeline[0]
            assert 'title' in timeline[0]
    
    def test_create_timeline_empty(self, analytics_service):
        """Test timeline creation with no activities"""
        timeline = analytics_service._create_activity_timeline([])
        
        assert isinstance(timeline, list)
        assert len(timeline) == 0
    
    def test_generate_insights(self, analytics_service, sample_deal, sample_activities_list):
        """Test insight generation"""
        sentiment_summary = {'dominant_sentiment': 'مثبت', 'sentiment_available': True}
        
        insights = analytics_service._generate_insights(
            sample_deal.to_dict(),
            sample_activities_list[:3],
            sentiment_summary,
            health_score=75,
            risk_indicators=[]
        )
        
        assert isinstance(insights, list)
        assert len(insights) > 0
        # Each insight should be a string
        assert all(isinstance(insight, str) for insight in insights)
    
    def test_generate_recommendations(self, analytics_service, sample_deal):
        """Test recommendation generation"""
        risks = [
            {'type': 'low_health', 'recommendation': 'توصیه تست'}
        ]
        
        recommendations = analytics_service._generate_recommendations(
            sample_deal.to_dict(),
            health_score=35,
            risk_indicators=risks
        )
        
        assert isinstance(recommendations, list)
        assert len(recommendations) > 0
        # Should include risk recommendations
        assert any('توصیه' in r for r in recommendations)
    
    def test_get_health_category(self, analytics_service):
        """Test health category labeling"""
        # High score
        category_high = analytics_service._get_health_category(85)
        assert category_high == 'سالم'
        
        # Medium score
        category_medium = analytics_service._get_health_category(55)
        assert category_medium == 'متوسط'
        
        # Low score
        category_low = analytics_service._get_health_category(25)
        assert category_low == 'در خطر'


class TestAnalyticsIntegration:
    """Test analytics service integration with other services"""
    
    def test_comprehensive_analysis_integration(self, analytics_service, test_repositories, sample_deal, sample_activities_list):
        """Test full comprehensive analysis workflow"""
        # Create deal and activities
        test_repositories.deals.create_deal(sample_deal)
        for activity in sample_activities_list[:5]:
            test_repositories.activities.create_activity(activity)
        
        # Run comprehensive analysis
        result = analytics_service.analyze_deal_comprehensive(sample_deal.Id)
        
        # Check result structure
        assert result is not None
        assert 'deal' in result or 'deal_id' in result
        assert 'health_score' in result
        assert 'insights' in result
        assert 'recommendations' in result
        
        # Validate health score
        assert isinstance(result['health_score'], int)
        assert 0 <= result['health_score'] <= 100