"""
tests/unit/test_models.py
-------------------------
Unit tests for data models
"""

import pytest
from datetime import datetime
from decimal import Decimal
import json


class TestDealModel:
    """Test Deal model"""
    
    def test_deal_creation(self, sample_deal):
        """Test creating a Deal instance"""
        assert sample_deal is not None
        assert sample_deal.Id is not None
        assert sample_deal.Title == "Test Deal"
    
    def test_deal_to_dict(self, sample_deal):
        """Test converting Deal to dictionary"""
        deal_dict = sample_deal.to_dict()
        
        assert isinstance(deal_dict, dict)
        assert deal_dict['Id'] == sample_deal.Id
        assert deal_dict['Title'] == sample_deal.Title
        assert deal_dict['Status'] == sample_deal.Status
    
    def test_deal_from_dict(self, sample_deal_dict):
        """Test creating Deal from dictionary"""
        from models.deal_model import Deal
        
        deal = Deal.from_dict(sample_deal_dict)
        
        assert deal.Id == sample_deal_dict['Id']
        assert deal.Title == sample_deal_dict['Title']
        assert deal.Status == sample_deal_dict['Status']
    
    def test_deal_datetime_serialization(self, sample_deal):
        """Test datetime fields are properly serialized"""
        deal_dict = sample_deal.to_dict()
        
        if sample_deal.RegisterTime:
            assert isinstance(deal_dict['RegisterTime'], str)
            # Should be ISO format
            datetime.fromisoformat(deal_dict['RegisterTime'])
    
    def test_deal_price_handling(self, sample_deal):
        """Test Decimal price handling"""
        assert isinstance(sample_deal.Price, Decimal)
        
        deal_dict = sample_deal.to_dict()
        # Price should be converted to float in dict
        assert isinstance(deal_dict['Price'], float)
    
    def test_deal_get_fields_as_dict(self, sample_deal):
        """Test parsing Fields JSON"""
        sample_deal.Fields = '{"custom_field": "value"}'
        
        fields = sample_deal.get_fields_as_dict()
        
        assert isinstance(fields, dict)
        assert 'custom_field' in fields
        assert fields['custom_field'] == "value"
    
    def test_deal_get_fields_empty(self, sample_deal):
        """Test parsing empty Fields"""
        sample_deal.Fields = None
        
        fields = sample_deal.get_fields_as_dict()
        
        assert isinstance(fields, dict)
        assert len(fields) == 0
    
    def test_deal_get_items_as_list(self, sample_deal):
        """Test parsing Items JSON"""
        sample_deal.Items = '[{"item": "test"}]'
        
        items = sample_deal.get_items_as_list()
        
        assert isinstance(items, list)
        assert len(items) == 1


class TestDealActivityModel:
    """Test DealActivity model"""
    
    def test_activity_creation(self, sample_activity):
        """Test creating a DealActivity instance"""
        assert sample_activity is not None
        assert sample_activity.id is not None
        assert sample_activity.title == "تماس تلفنی"
    
    def test_activity_to_dict(self, sample_activity):
        """Test converting DealActivity to dictionary"""
        activity_dict = sample_activity.to_dict()
        
        assert isinstance(activity_dict, dict)
        assert activity_dict['id'] == sample_activity.id
        assert activity_dict['title'] == sample_activity.title
        assert activity_dict['dealid'] == sample_activity.dealid
    
    def test_activity_from_dict(self, sample_activity_dict):
        """Test creating DealActivity from dictionary"""
        from models.deal_model import DealActivity
        
        activity = DealActivity.from_dict(sample_activity_dict)
        
        assert activity.id == sample_activity_dict['id']
        assert activity.title == sample_activity_dict['title']
        assert activity.dealid == sample_activity_dict['dealid']
    
    def test_activity_get_combined_text(self, sample_activity):
        """Test getting combined text for sentiment analysis"""
        combined = sample_activity.get_combined_text()
        
        assert isinstance(combined, str)
        assert sample_activity.title in combined
        assert sample_activity.note in combined
    
    def test_activity_get_combined_text_empty(self):
        """Test combined text with empty fields"""
        from models.deal_model import DealActivity
        
        activity = DealActivity(id='test', title='', note='', resultnote='')
        combined = activity.get_combined_text()
        
        assert combined == ""
    
    def test_activity_boolean_fields(self, sample_activity):
        """Test boolean field handling"""
        assert isinstance(sample_activity.isdone, bool)
        
        activity_dict = sample_activity.to_dict()
        assert isinstance(activity_dict['isdone'], bool)


class TestCRMAgentModel:
    """Test CRMAgent model"""
    
    def test_agent_creation(self, sample_agent):
        """Test creating a CRMAgent instance"""
        assert sample_agent is not None
        assert sample_agent.id is not None
        assert sample_agent.ownername == "علی احمدی"
    
    def test_agent_to_dict(self, sample_agent):
        """Test converting CRMAgent to dictionary"""
        agent_dict = sample_agent.to_dict()
        
        assert isinstance(agent_dict, dict)
        assert agent_dict['id'] == sample_agent.id
        assert agent_dict['ownername'] == sample_agent.ownername
        assert agent_dict['role'] == sample_agent.role
    
    def test_agent_from_dict(self, sample_agent_dict):
        """Test creating CRMAgent from dictionary"""
        from models.deal_model import CRMAgent
        
        agent = CRMAgent.from_dict(sample_agent_dict)
        
        assert agent.id == sample_agent_dict['id']
        assert agent.ownername == sample_agent_dict['ownername']
        assert agent.role == sample_agent_dict['role']
    
    def test_agent_get_display_name(self, sample_agent):
        """Test getting agent display name"""
        display_name = sample_agent.get_display_name()
        
        assert isinstance(display_name, str)
        assert len(display_name) > 0
        # Should prefer ownername
        assert display_name == sample_agent.ownername
    
    def test_agent_get_display_name_fallback(self):
        """Test display name fallback when ownername is empty"""
        from models.deal_model import CRMAgent
        
        agent = CRMAgent(id='test-id', ownername='', groupowner='تیم فروش')
        display_name = agent.get_display_name()
        
        # Should fall back to groupowner
        assert display_name == 'تیم فروش'
    
    def test_agent_get_contact_number(self, sample_agent):
        """Test getting primary contact number"""
        contact = sample_agent.get_contact_number()
        
        assert isinstance(contact, str)
        # Should return mobilephone if available
        assert contact == sample_agent.mobilephone


class TestSentimentAnalysisModel:
    """Test SentimentAnalysis model"""
    
    def test_sentiment_creation(self, sample_sentiment):
        """Test creating a SentimentAnalysis instance"""
        assert sample_sentiment is not None
        assert sample_sentiment.text is not None
        assert sample_sentiment.label == 'positive'
    
    def test_sentiment_to_dict(self, sample_sentiment):
        """Test converting SentimentAnalysis to dictionary"""
        sentiment_dict = sample_sentiment.to_dict()
        
        assert isinstance(sentiment_dict, dict)
        assert sentiment_dict['text'] == sample_sentiment.text
        assert sentiment_dict['label'] == sample_sentiment.label
        assert sentiment_dict['score'] == sample_sentiment.score
    
    def test_sentiment_from_dict(self, sample_sentiment_dict):
        """Test creating SentimentAnalysis from dictionary"""
        from models.sentiment_model import SentimentAnalysis
        
        sentiment = SentimentAnalysis.from_dict(sample_sentiment_dict)
        
        assert sentiment.text == sample_sentiment_dict['text']
        assert sentiment.label == sample_sentiment_dict['label']
        assert sentiment.score == sample_sentiment_dict['score']
    
    def test_sentiment_is_positive(self, sample_sentiment):
        """Test checking if sentiment is positive"""
        sample_sentiment.label = 'مثبت'
        sample_sentiment.score = 0.9
        
        assert sample_sentiment.is_positive() is True
    
    def test_sentiment_is_negative(self):
        """Test checking if sentiment is negative"""
        from models.sentiment_model import SentimentAnalysis
        
        sentiment = SentimentAnalysis(
            text="Test",
            label='negative',
            score=0.2
        )
        
        assert sentiment.is_negative() is True
    
    def test_sentiment_is_neutral(self):
        """Test checking if sentiment is neutral"""
        from models.sentiment_model import SentimentAnalysis
        
        sentiment = SentimentAnalysis(
            text="Test",
            label='خنثی',
            score=0.5
        )
        
        assert sentiment.is_neutral() is True
    
    def test_sentiment_datetime_handling(self, sample_sentiment):
        """Test datetime field handling"""
        if sample_sentiment.processed_at:
            sentiment_dict = sample_sentiment.to_dict()
            
            # Should be ISO format string
            assert isinstance(sentiment_dict['processed_at'], str)
            datetime.fromisoformat(sentiment_dict['processed_at'])


class TestModelSerialization:
    """Test model serialization/deserialization"""
    
    def test_deal_round_trip(self, sample_deal):
        """Test Deal to_dict -> from_dict round trip"""
        from models.deal_model import Deal
        
        # Convert to dict
        deal_dict = sample_deal.to_dict()
        
        # Convert back to object
        restored_deal = Deal.from_dict(deal_dict)
        
        # Should have same values
        assert restored_deal.Id == sample_deal.Id
        assert restored_deal.Title == sample_deal.Title
        assert restored_deal.Status == sample_deal.Status
    
    def test_activity_round_trip(self, sample_activity):
        """Test DealActivity to_dict -> from_dict round trip"""
        from models.deal_model import DealActivity
        
        activity_dict = sample_activity.to_dict()
        restored = DealActivity.from_dict(activity_dict)
        
        assert restored.id == sample_activity.id
        assert restored.title == sample_activity.title
        assert restored.dealid == sample_activity.dealid
    
    def test_agent_round_trip(self, sample_agent):
        """Test CRMAgent to_dict -> from_dict round trip"""
        from models.deal_model import CRMAgent
        
        agent_dict = sample_agent.to_dict()
        restored = CRMAgent.from_dict(agent_dict)
        
        assert restored.id == sample_agent.id
        assert restored.ownername == sample_agent.ownername
        assert restored.role == sample_agent.role