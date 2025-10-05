"""
tests/unit/test_deal_service.py
-------------------------------
Unit tests for DealService
"""

import pytest
from datetime import datetime, timedelta


class TestDealService:
    """Test DealService functionality"""
    
    def test_get_deal_exists(self, deal_service, test_repositories, sample_deal):
        """Test getting an existing deal"""
        # Create deal first
        test_repositories.deals.create_deal(sample_deal)
        
        # Get deal using service
        result = deal_service.get_deal(sample_deal.Id)
        
        assert result is not None
        assert result['Id'] == sample_deal.Id
        assert result['Title'] == sample_deal.Title
    
    def test_get_deal_not_found(self, deal_service):
        """Test getting non-existent deal returns None"""
        result = deal_service.get_deal('nonexistent-deal-xyz')
        
        assert result is None
    
    def test_get_all_deals(self, deal_service, test_repositories, sample_deals_list):
        """Test getting all deals"""
        # Create some deals
        for deal in sample_deals_list[:3]:
            test_repositories.deals.create_deal(deal)
        
        # Get all deals
        deals = deal_service.get_all_deals()
        
        assert isinstance(deals, list)
        assert len(deals) >= 3
    
    def test_get_deals_by_status(self, deal_service, test_repositories, sample_deals_list):
        """Test filtering deals by status"""
        # Create deals with different statuses
        for deal in sample_deals_list[:5]:
            test_repositories.deals.create_deal(deal)
        
        # Get deals with specific status
        active_deals = deal_service.get_deals_by_status('در حال پیگیری')
        
        assert isinstance(active_deals, list)
        # All returned deals should have requested status
        for deal in active_deals:
            assert deal['Status'] == 'در حال پیگیری'
    
    def test_get_deals_summary(self, deal_service, test_repositories, sample_deals_list):
        """Test getting deals summary statistics"""
        # Create sample deals
        for deal in sample_deals_list[:5]:
            test_repositories.deals.create_deal(deal)
        
        # Get summary
        summary = deal_service.get_deals_summary(days=30)
        
        assert 'total_deals' in summary
        assert 'active_deals' in summary
        assert 'closed_deals' in summary
        assert 'total_value' in summary
        assert isinstance(summary['total_deals'], int)
    
    def test_get_deals_summary_empty(self, deal_service):
        """Test summary with no deals"""
        # Clear any existing deals or use isolated test
        summary = deal_service.get_deals_summary(days=30)
        
        # Should return error or zero counts, not crash
        assert summary is not None
    
    def test_get_deal_timeline(self, deal_service, test_repositories, sample_deal, sample_activities_list):
        """Test getting deal timeline"""
        # Create deal and activities
        test_repositories.deals.create_deal(sample_deal)
        for activity in sample_activities_list[:5]:
            test_repositories.activities.create_activity(activity)
        
        # Get timeline
        timeline = deal_service.get_deal_timeline(sample_deal.Id)
        
        assert timeline is not None
        assert 'timeline' in timeline
        assert 'total_events' in timeline
        assert isinstance(timeline['timeline'], list)
        assert len(timeline['timeline']) > 0
    
    def test_get_deal_timeline_not_found(self, deal_service):
        """Test timeline for non-existent deal"""
        timeline = deal_service.get_deal_timeline('nonexistent-deal')
        
        assert 'error' in timeline
    
    def test_calculate_deal_duration(self, deal_service, sample_deal):
        """Test deal duration calculation"""
        # Set up deal with known dates
        sample_deal.RegisterTime = datetime.now() - timedelta(days=30)
        sample_deal.LastUpdateTime = datetime.now()
        
        duration = deal_service._calculate_deal_duration(sample_deal.to_dict())
        
        assert duration is not None
        assert isinstance(duration, int)
        assert duration >= 30  # Should be at least 30 days
    
    def test_calculate_deal_duration_no_dates(self, deal_service, sample_deal):
        """Test duration calculation with missing dates"""
        sample_deal.RegisterTime = None
        
        duration = deal_service._calculate_deal_duration(sample_deal.to_dict())
        
        # Should handle gracefully
        assert duration is None or isinstance(duration, int)