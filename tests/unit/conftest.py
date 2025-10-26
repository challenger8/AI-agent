"""
tests/unit/conftest.py
-----------------------------
Unit test fixtures - CORRECT SAMPLE DATA matching actual models
"""
import pytest
import sys
import os
import uuid
from pathlib import Path
from unittest.mock import Mock
from decimal import Decimal
from datetime import datetime, timedelta

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from models.deal_model import Deal, DealActivity, CRMAgent
from models.sentiment_model import SentimentAnalysis


# ============================================================================
# SAMPLE DATA FIXTURES - CORRECT DEFINITIONS
# ============================================================================

@pytest.fixture(scope="function")
def sample_deal_dict():
    """Sample deal as dictionary - matches Deal model"""
    return {
        'Id': str(uuid.uuid4()),
        'Title': 'نرم افزار سازمانی',
        'Description': 'توسعه و پیاده سازی',
        'RegisterTime': datetime.now(),
        'Price': Decimal('100000.00'),
        'Status': 'در حال پیگیری',
        'PipelineStageId': 'stage-001',
        'PipelineId': 'pipeline-001',
        'Probability': 0.75,
        'ContactId': 'contact-001',
        'OwnerId': 'owner-001',
        'CreatorId': 'creator-001',
        'Pin': False,
        'IsIdle': False,
        'MobilePhone': '09123456789',
        'Fields': None,
        'Items': None
    }


@pytest.fixture(scope="function")
def sample_deal(sample_deal_dict):
    """Sample Deal model instance"""
    return Deal.from_dict(sample_deal_dict)


@pytest.fixture(scope="function")
def sample_activity_dict(sample_deal):
    """Sample activity as dictionary - matches DealActivity model"""
    return {
        'id': str(uuid.uuid4()),
        'title': 'تماس تلفنی',
        'note': 'بحث در مورد قیمت و شرایط',
        'resultnote': 'مشتری علاقمند است',
        'activitytypeid': 'type-call',
        'isprivate': False,
        'isdone': False,  # Pending activity
        'ispinned': False,
        'duedate': datetime.now() + timedelta(days=3),
        'finishdate': None,
        'donedate': None,
        'registerdate': datetime.now(),
        'lastupdatetime': datetime.now(),
        'dealid': sample_deal.Id,
        'creatorid': 'creator-001',
        'ownerid': 'owner-001',
        'updaterid': 'updater-001',
        'sentiment_score': 0.85,
        'sentiment_label': 'positive'
    }


@pytest.fixture(scope="function")
def sample_activity(sample_activity_dict):
    """Sample DealActivity model instance"""
    return DealActivity.from_dict(sample_activity_dict)


@pytest.fixture(scope="function")
def sample_agent_dict():
    """Sample agent as dictionary - matches CRMAgent model"""
    return {
        'id': str(uuid.uuid4()),
        'groupowner': 'تیم فروش',
        'ownername': 'علی احمدی',
        'adminid': 'admin-001',
        'role': 'فروشنده',
        'phone': '02112345678',
        'mobilephone': '09123456789',
        'personalid': '1234567890',
        'groupphone': '02187654321'
    }


@pytest.fixture(scope="function")
def sample_agent(sample_agent_dict):
    """Sample CRMAgent model instance"""
    return CRMAgent.from_dict(sample_agent_dict)


@pytest.fixture(scope="function")
def sample_sentiment_dict(sample_deal, sample_activity):
    """Sample sentiment as dictionary - matches SentimentAnalysis model"""
    return {
        'id': str(uuid.uuid4()),
        'text': 'مشتری بسیار راضی از محصول است',
        'language': 'fa',
        'label': 'positive',  # English: positive, negative, neutral
        'score': 0.95,
        'polarity': None,
        'subjectivity': None,
        'model_name': 'sentiment-model',
        'model_version': '1.0',
        'processed_at': datetime.now(),
        'deal_id': sample_deal.Id,
        'activity_id': sample_activity.id
    }


@pytest.fixture(scope="function")
def sample_sentiment(sample_sentiment_dict):
    """Sample SentimentAnalysis model instance"""
    return SentimentAnalysis.from_dict(sample_sentiment_dict)


# ============================================================================
# LISTS OF SAMPLE DATA
# ============================================================================

@pytest.fixture(scope="function")
def sample_deals_list(sample_deal):
    """List of sample deals"""
    statuses = ['در حال پیگیری', 'در حال مذاکره', 'پیش از توافق']
    deals = []
    
    for i in range(3):
        deal_dict = {
            'Id': str(uuid.uuid4()),
            'Title': f'پروژه {i+1}',
            'Description': f'توضیح پروژه {i+1}',
            'RegisterTime': datetime.now(),
            'Price': Decimal(str(50000 * (i+1))),
            'Status': statuses[i],
            'OwnerId': 'owner-001',
            'ContactId': f'contact-{i:03d}'
        }
        deals.append(Deal.from_dict(deal_dict))
    
    return deals


@pytest.fixture(scope="function")
def sample_activities_list(sample_deal):
    """List of sample activities"""
    activities = []
    types = ['call', 'email', 'meeting']
    
    for i in range(3):
        activity_dict = {
            'id': str(uuid.uuid4()),
            'title': f'فعالیت {i+1}',
            'note': f'توضیح فعالیت {i+1}',
            'resultnote': f'نتیجه فعالیت {i+1}',
            'activitytypeid': f'type-{types[i]}',
            'isdone': i > 1,  # Last one is done
            'dealid': sample_deal.Id,
            'sentiment_score': 0.7 + (i * 0.1),
            'sentiment_label': 'positive'
        }
        activities.append(DealActivity.from_dict(activity_dict))
    
    return activities


@pytest.fixture(scope="function")
def sample_agents_list():
    """List of sample agents"""
    agents = []
    roles = ['فروشنده', 'مدیر فروش', 'متخصص']
    names = ['علی احمدی', 'فاطمه موسوی', 'محمد حسینی']
    
    for i in range(3):
        agent_dict = {
            'id': str(uuid.uuid4()),
            'groupowner': 'تیم فروش',
            'ownername': names[i],
            'adminid': 'admin-001',
            'role': roles[i],
            'phone': f'0211234567{i}',
            'mobilephone': f'0912345678{i}',
            'personalid': f'{1000000000 + i}',
            'groupphone': '02187654321'
        }
        agents.append(CRMAgent.from_dict(agent_dict))
    
    return agents


# ============================================================================
# MOCK REPOSITORY - Uses real model instances
# ============================================================================

@pytest.fixture(scope="function")
def test_repositories(sample_deal, sample_activity, sample_agent, 
                      sample_deals_list, sample_activities_list, 
                      sample_agents_list, sample_sentiment):
    """Mock repository manager with real model instances"""
    
    repos = Mock()
    
    # ===== DEAL REPOSITORY =====
    repos.deals = Mock()
    repos.deals.create_deal = Mock(return_value=1)
    repos.deals.get_deal_by_id = Mock(return_value=sample_deal)
    repos.deals.get_all_deals = Mock(return_value=sample_deals_list)
    repos.deals.update_deal = Mock(return_value=True)
    repos.deals.delete_deal = Mock(return_value=True)
    repos.deals.get_deals_by_status = Mock(return_value=[sample_deal])
    repos.deals.get_deals_statistics = Mock(return_value={
        'total_deals': 3,
        'by_status': {'در حال پیگیری': 1},
        'total_value': Decimal('350000.00')
    })
    
    # ===== ACTIVITY REPOSITORY =====
    repos.activities = Mock()
    repos.activities.create_activity = Mock(return_value=1)
    repos.activities.get_activity_by_id = Mock(return_value=sample_activity)
    repos.activities.get_all_activities = Mock(return_value=sample_activities_list)
    repos.activities.get_activities_by_deal = Mock(return_value=sample_activities_list)
    repos.activities.update_activity = Mock(return_value=True)
    repos.activities.delete_activity = Mock(return_value=True)
    repos.activities.update_activity_sentiment = Mock(return_value=sample_activity)
    repos.activities.get_pending_activities = Mock(return_value=[sample_activities_list[0]])
    repos.activities.get_activities_by_date_range = Mock(return_value=sample_activities_list)
    
    # ===== AGENT REPOSITORY =====
    repos.agents = Mock()
    repos.agents.create_agent = Mock(return_value=1)
    repos.agents.get_agent_by_id = Mock(return_value=sample_agent)
    repos.agents.get_all_agents = Mock(return_value=sample_agents_list)
    repos.agents.update_agent = Mock(return_value=True)
    repos.agents.delete_agent = Mock(return_value=True)
    repos.agents.get_agents_by_role = Mock(return_value=[sample_agent])
    repos.agents.get_agent_statistics = Mock(return_value={
        'total_agents': 3,
        'by_role': {'فروشنده': 1}
    })
    
    # ===== SENTIMENT REPOSITORY =====
    repos.sentiment = Mock()
    repos.sentiment.save_sentiment = Mock(return_value=1)
    repos.sentiment.get_sentiment_by_activity = Mock(return_value=sample_sentiment)
    repos.sentiment.get_sentiments_by_deal = Mock(return_value=[sample_sentiment])
    repos.sentiment.update_sentiment = Mock(return_value=True)
    repos.sentiment.get_sentiment_statistics = Mock(return_value={
        'positive': 10,
        'negative': 2,
        'neutral': 3
    })
    
    # ===== CONTEXT MANAGER =====
    repos.__enter__ = Mock(return_value=repos)
    repos.__exit__ = Mock(return_value=False)
    
    # ===== Helper methods =====
    repos.get_deal_with_details = Mock(return_value={
        'deal': sample_deal,
        'activities': sample_activities_list,
        'sentiment_summary': {'positive': 2, 'neutral': 1}
    })
    
    return repos


# ============================================================================
# MOCK DATABASE
# ============================================================================

@pytest.fixture(scope="function")
def mock_db_manager():
    """Mock database manager"""
    mock_db = Mock()
    mock_db.execute_query = Mock(return_value=[])
    mock_db.execute_insert = Mock(return_value=1)
    mock_db.execute_update = Mock(return_value=1)
    mock_db.execute_delete = Mock(return_value=1)
    mock_db.test_connection = Mock(return_value=True)
    mock_db.close = Mock()
    return mock_db


# ============================================================================
# MOCK SERVICES
# ============================================================================

@pytest.fixture(scope="function")
def mock_sentiment_service():
    """Mock sentiment service"""
    mock_service = Mock()
    mock_service.model_loaded = True
    mock_service.available = True
    mock_service.analyze_text = Mock(return_value={
        "sentiment": "positive",
        "confidence": 0.85,
        "text_preview": "Sample text..."
    })
    mock_service.analyze_batch = Mock(return_value=[
        {"sentiment": "positive", "confidence": 0.85},
        {"sentiment": "negative", "confidence": 0.75},
        {"sentiment": "neutral", "confidence": 0.65}
    ])
    return mock_service


@pytest.fixture(scope="function")
def mock_cache_service():
    """Mock cache service"""
    mock_cache = Mock()
    mock_cache.get = Mock(return_value=None)
    mock_cache.set = Mock(return_value=True)
    mock_cache.delete = Mock(return_value=True)
    mock_cache.is_available = Mock(return_value=False)
    return mock_cache


# ============================================================================
# TEST CONFIGURATION
# ============================================================================

@pytest.fixture(scope="session")
def test_config():
    """Test configuration"""
    return {
        'test_db_name': 'persian_crm_test_db',
        'health_score_threshold_high': 70,
        'health_score_threshold_medium': 40,
        'stale_activity_days': 14,
        'aging_deal_days': 60
    }


@pytest.fixture(scope="session")
def unit_test_config():
    """Unit test configuration"""
    return {
        'test_db_name': 'persian_crm_test_db',
        'use_mocks': True
    }


# ============================================================================
# CLEANUP
# ============================================================================

@pytest.fixture(scope="function", autouse=True)
def cleanup_after_test():
    """Cleanup after each test"""
    yield