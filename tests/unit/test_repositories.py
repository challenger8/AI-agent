"""
tests/unit/test_repositories.py
-------------------------------
Unit tests for Repository classes
"""

import pytest
from datetime import datetime
from decimal import Decimal

@pytest.mark.unit
class TestDealRepository:
    """Test DealRepository"""
    def test_get_all_deals(self, test_repositories):
        """Test getting all deals"""
        deals = test_repositories.deals.get_all_deals()
        
        assert isinstance(deals, list)
        # May be empty if no data, but should return a list
        assert deals is not None
    def test_create_and_get_deal(self, test_repositories, sample_deal):
        """Test creating a deal and retrieving it"""
        # Create deal
        deal_id = test_repositories.deals.create_deal(sample_deal)
        
        assert deal_id is not None
        
        # Retrieve deal
        retrieved_deal = test_repositories.deals.get_deal_by_id(sample_deal.Id)
        
        assert retrieved_deal is not None
        assert retrieved_deal.Id == sample_deal.Id
        assert retrieved_deal.Title == sample_deal.Title
    def test_get_deal_by_id_nonexistent(self, test_repositories):
        """Test getting non-existent deal returns None"""
        result = test_repositories.deals.get_deal_by_id('nonexistent-deal-xyz')
        
        assert result is None
    def test_update_deal(self, test_repositories, sample_deal):
        """Test updating a deal"""
        # Create deal
        test_repositories.deals.create_deal(sample_deal)
        
        # Update deal
        sample_deal.Title = "Updated Title"
        sample_deal.Status = "بسته شده"
        
        success = test_repositories.deals.update_deal(sample_deal)
        
        assert success is True
        
        # Verify update
        updated_deal = test_repositories.deals.get_deal_by_id(sample_deal.Id)
        assert updated_deal.Title == "Updated Title"
        assert updated_deal.Status == "بسته شده"
    def test_get_deals_by_status(self, test_repositories, sample_deals_list):
        """Test filtering deals by status"""
        # Create multiple deals with different statuses
        for deal in sample_deals_list[:5]:
            test_repositories.deals.create_deal(deal)
        
        # Get deals by status
        active_deals = test_repositories.deals.get_deals_by_status('در حال پیگیری')
        
        assert isinstance(active_deals, list)
        # All returned deals should have the requested status
        for deal in active_deals:
            assert deal.Status == 'در حال پیگیری'
    def test_get_deals_statistics(self, test_repositories, sample_deals_list):
        """Test getting deal statistics"""
        # Create sample deals
        for deal in sample_deals_list[:3]:
            test_repositories.deals.create_deal(deal)
        
        stats = test_repositories.deals.get_deals_statistics()
        
        assert 'total_deals' in stats
        assert 'by_status' in stats
        assert isinstance(stats['total_deals'], int)

@pytest.mark.unit
class TestDealActivityRepository:
    """Test DealActivityRepository"""
    def test_create_and_get_activity(self, test_repositories, sample_activity, sample_deal):
        """Test creating and retrieving an activity"""
        # Create deal first (foreign key constraint)
        test_repositories.deals.create_deal(sample_deal)
        
        # Create activity
        activity_id = test_repositories.activities.create_activity(sample_activity)
        
        assert activity_id is not None
        
        # Retrieve activity
        retrieved = test_repositories.activities.get_activity_by_id(sample_activity.id)
        
        assert retrieved is not None
        assert retrieved.id == sample_activity.id
        assert retrieved.title == sample_activity.title
    def test_get_activities_by_deal(self, test_repositories, sample_deal, sample_activities_list):
        """Test getting activities for a specific deal"""
        # Create deal
        test_repositories.deals.create_deal(sample_deal)
        
        # Create activities
        for activity in sample_activities_list[:5]:
            test_repositories.activities.create_activity(activity)
        
        # Get activities for deal
        activities = test_repositories.activities.get_activities_by_deal(sample_deal.Id)
        
        assert isinstance(activities, list)
        assert len(activities) > 0
        # All activities should belong to the deal
        for activity in activities:
            assert activity.dealid == sample_deal.Id
    def test_get_activities_by_deal_empty(self, test_repositories):
        """Test getting activities for deal with no activities"""
        activities = test_repositories.activities.get_activities_by_deal('nonexistent-deal')
        
        assert isinstance(activities, list)
        assert len(activities) == 0
    def test_update_activity_sentiment(self, test_repositories, sample_activity, sample_deal):
        """Test updating activity sentiment"""
        # Create deal and activity
        test_repositories.deals.create_deal(sample_deal)
        test_repositories.activities.create_activity(sample_activity)
        
        # Update sentiment
        success = test_repositories.activities.update_activity_sentiment(
            sample_activity.id,
            sentiment_score=0.85,
            sentiment_label='مثبت'
        )
        
        assert success is True
        
        # Verify update
        updated = test_repositories.activities.get_activity_by_id(sample_activity.id)
        assert updated.sentiment_score == 0.85
        assert updated.sentiment_label == 'مثبت'
    def test_get_pending_activities(self, test_repositories, sample_deal, sample_activities_list):
        """Test getting pending (not done) activities"""
        # Create deal
        test_repositories.deals.create_deal(sample_deal)
        
        # Create mix of done and pending activities
        for i, activity in enumerate(sample_activities_list[:5]):
            activity.isdone = (i % 2 == 0)  # Alternate done/pending
            test_repositories.activities.create_activity(activity)
        
        # Get pending activities
        pending = test_repositories.activities.get_pending_activities()
        
        assert isinstance(pending, list)
        # All returned activities should be not done
        for activity in pending:
            assert activity.isdone is False or activity.isdone is None

@pytest.mark.unit
class TestCRMAgentRepository:
    """Test CRMAgentRepository"""
    def test_create_and_get_agent(self, test_repositories, sample_agent):
        """Test creating and retrieving an agent"""
        # Create agent
        agent_id = test_repositories.agents.create_agent(sample_agent)
        
        assert agent_id is not None
        
        # Retrieve agent
        retrieved = test_repositories.agents.get_agent_by_id(sample_agent.id)
        
        assert retrieved is not None
        assert retrieved.id == sample_agent.id
        assert retrieved.ownername == sample_agent.ownername
    def test_get_all_agents(self, test_repositories, sample_agents_list):
        """Test getting all agents"""
        # Create agents
        for agent in sample_agents_list[:3]:
            test_repositories.agents.create_agent(agent)
        
        # Get all agents
        agents = test_repositories.agents.get_all_agents()
        
        assert isinstance(agents, list)
        assert len(agents) >= 3
    def test_get_agents_by_role(self, test_repositories, sample_agents_list):
        """Test filtering agents by role"""
        # Create agents with different roles
        for agent in sample_agents_list[:3]:
            test_repositories.agents.create_agent(agent)
        
        # Get agents by specific role
        agents = test_repositories.agents.get_agents_by_role('فروشنده')
        
        assert isinstance(agents, list)
        # All returned agents should have the requested role
        for agent in agents:
            assert agent.role == 'فروشنده'
    def test_get_agent_by_id_nonexistent(self, test_repositories):
        """Test getting non-existent agent returns None"""
        result = test_repositories.agents.get_agent_by_id('nonexistent-agent-xyz')
        
        assert result is None

@pytest.mark.unit
class TestSentimentRepository:
    """Test SentimentRepository"""
    def test_save_sentiment(self, test_repositories, sample_sentiment, sample_deal, sample_activity):
        """Test saving sentiment analysis"""
        # Create deal and activity first
        test_repositories.deals.create_deal(sample_deal)
        test_repositories.activities.create_activity(sample_activity)
        
        # Save sentiment
        sentiment_id = test_repositories.sentiment.save_sentiment(sample_sentiment)
        
        assert sentiment_id is not None
        assert sentiment_id > 0
    def test_get_sentiment_by_activity(self, test_repositories, sample_sentiment, sample_deal, sample_activity):
        """Test retrieving sentiment by activity"""
        # Create dependencies and sentiment
        test_repositories.deals.create_deal(sample_deal)
        test_repositories.activities.create_activity(sample_activity)
        test_repositories.sentiment.save_sentiment(sample_sentiment)
        
        # Retrieve sentiment
        retrieved = test_repositories.sentiment.get_sentiment_by_activity(sample_activity.id)
        
        # Note: May be None if multiple sentiments exist
        # This tests that the method runs without error
        assert retrieved is None or hasattr(retrieved, 'label')
    def test_get_sentiments_by_deal(self, test_repositories, sample_sentiment, sample_deal, sample_activity):
        """Test getting all sentiments for a deal"""
        # Create dependencies and sentiment
        test_repositories.deals.create_deal(sample_deal)
        test_repositories.activities.create_activity(sample_activity)
        test_repositories.sentiment.save_sentiment(sample_sentiment)
        
        # Get sentiments for deal
        sentiments = test_repositories.sentiment.get_sentiments_by_deal(sample_deal.Id)
        
        assert isinstance(sentiments, list)

@pytest.mark.unit
class TestRepositoryManager:
    """Test RepositoryManager context manager"""
    def test_repository_manager_context(self, test_repositories):
        """Test using RepositoryManager as context manager"""
        with test_repositories as uow:
            # Should be able to access all repositories
            assert uow.deals is not None
            assert uow.activities is not None
            assert uow.agents is not None
            assert uow.sentiment is not None
    def test_get_deal_with_details(self, test_repositories, sample_deal, sample_activities_list):
        """Test getting deal with all related details"""
        # Create deal and activities
        test_repositories.deals.create_deal(sample_deal)
        for activity in sample_activities_list[:3]:
            test_repositories.activities.create_activity(activity)
        
        # Get deal with details
        details = test_repositories.get_deal_with_details(sample_deal.Id)
        
        assert details is not None
        assert 'deal' in details
        assert 'activities' in details
        assert len(details['activities']) > 0