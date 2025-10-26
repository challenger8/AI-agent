"""
tests/unit/conftest.py
======================
Unit test fixtures (mocks only - no real dependencies)

This file contains:
- Mock database manager
- Mock repositories
- Mock services
- Sample data for testing (Deal, Activity, Agent, Sentiment models)
- Unit test configuration

Loaded AFTER tests/conftest.py (root)
Only visible to tests in tests/unit/
"""

import uuid
import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import Mock, MagicMock

# ============================================================================
# IMPORTS
# ============================================================================

from models.deal_model import Deal, DealActivity, CRMAgent
from models.sentiment_model import SentimentAnalysis
from services.deal_service import DealService
from services.sentiment_service import SentimentService
from services.analytics_service import AnalyticsService


# ============================================================================
# MOCK DATABASE & REPOSITORIES
# ============================================================================

@pytest.fixture
def mock_db_manager():
    """
    Mock database manager for unit tests
    
    No real database connection - all operations are mocked
    """
    mock_db = Mock()
    
    # Query operations
    mock_db.execute_query = Mock(return_value=[])
    mock_db.execute_insert = Mock(return_value=str(uuid.uuid4()))
    mock_db.execute_update = Mock(return_value=1)
    mock_db.execute_delete = Mock(return_value=1)
    mock_db.execute_batch_insert = Mock(return_value=True)
    
    # Connection management
    mock_db.test_connection = Mock(return_value=True)
    mock_db.close = Mock()
    mock_db.get_connection = Mock()
    
    # Statistics
    mock_db.get_database_stats = Mock(return_value={
        'deals_count': 0,
        'deal_activities_count': 0,
        'crm_agents_count': 0,
        'database_size': '0 MB'
    })
    
    # Context manager support
    mock_db.__enter__ = Mock(return_value=mock_db)
    mock_db.__exit__ = Mock(return_value=False)
    
    return mock_db


@pytest.fixture
def mock_repositories():
    """
    Mock repository manager for unit tests
    
    Provides mocked access to all repositories
    """
    repos = Mock()
    
    # Repository mock objects
    repos.deals = Mock()
    repos.activities = Mock()
    repos.agents = Mock()
    repos.sentiment = Mock()
    
    # Context manager support (for 'with' statements)
    repos.__enter__ = Mock(return_value=repos)
    repos.__exit__ = Mock(return_value=False)
    
    # Method mocks
    repos.deals.create_deal = Mock(return_value=str(uuid.uuid4()))
    repos.deals.get_deal_by_id = Mock(return_value=None)
    repos.deals.get_all_deals = Mock(return_value=[])
    repos.deals.update_deal = Mock(return_value=True)
    repos.deals.delete_deal = Mock(return_value=True)
    repos.deals.get_deals_by_status = Mock(return_value=[])
    repos.deals.get_deals_statistics = Mock(return_value={})
    
    repos.activities.create_activity = Mock(return_value=str(uuid.uuid4()))
    repos.activities.get_activity_by_id = Mock(return_value=None)
    repos.activities.get_activities_by_deal = Mock(return_value=[])
    repos.activities.get_all_activities = Mock(return_value=[])
    
    repos.agents.create_agent = Mock(return_value=str(uuid.uuid4()))
    repos.agents.get_agent_by_id = Mock(return_value=None)
    repos.agents.get_all_agents = Mock(return_value=[])
    
    repos.sentiment.save_sentiment = Mock(return_value=str(uuid.uuid4()))
    repos.sentiment.get_sentiment_by_activity = Mock(return_value=None)
    repos.sentiment.get_sentiments_by_deal = Mock(return_value=[])
    
    return repos


# ============================================================================
# MOCK SERVICES
# ============================================================================

@pytest.fixture
def mock_sentiment_service():
    """
    Mock SentimentService for unit tests
    
    Pre-configured with mock responses
    """
    mock_service = Mock()
    
    # Service status
    mock_service.model_loaded = True
    mock_service.available = True
    mock_service.enabled = True
    
    # Text analysis methods
    mock_service.analyze_text = Mock(return_value={
        "sentiment": "positive",
        "confidence": 0.85,
        "text_preview": "Sample text...",
        "language": "fa"
    })
    
    mock_service.analyze_batch = Mock(return_value=[
        {"sentiment": "positive", "confidence": 0.85},
        {"sentiment": "negative", "confidence": 0.75},
        {"sentiment": "neutral", "confidence": 0.65}
    ])
    
    # Activity analysis
    mock_service.analyze_activities_sentiment = Mock(return_value={
        "total_activities": 3,
        "analyzed_activities": 3,
        "sentiment_distribution": {
            "positive": 1,
            "negative": 1,
            "neutral": 1
        }
    })
    
    # Trends
    mock_service.get_sentiment_trends = Mock(return_value={
        "trends": [],
        "period_days": 30
    })
    
    # Cache operations
    mock_service.clear_sentiment_cache = Mock(return_value=10)
    mock_service.get_cache_stats = Mock(return_value={
        'model_loaded': True,
        'available': True,
        'cache_size': 0
    })
    
    return mock_service


@pytest.fixture
def mock_cache_service():
    """
    Mock CacheService for unit tests
    
    Simulates cache operations without Redis
    """
    mock_cache = Mock()
    
    # Status
    mock_cache.enabled = True
    mock_cache.is_available = Mock(return_value=False)
    
    # Cache operations
    mock_cache.get = Mock(return_value=None)
    mock_cache.set = Mock(return_value=True)
    mock_cache.delete = Mock(return_value=True)
    mock_cache.clear_all = Mock(return_value=True)
    mock_cache.delete_pattern = Mock(return_value=0)
    
    # Utilities
    mock_cache.generate_key = Mock(side_effect=lambda *args: ":".join(str(a) for a in args))
    mock_cache.hash_text = Mock(side_effect=lambda x: f"hash_{hash(x)}")
    
    # Statistics
    mock_cache.get_stats = Mock(return_value={
        'enabled': True,
        'available': False,
        'total_keys': 0,
        'used_memory': '0B'
    })
    
    return mock_cache


# ============================================================================
# SAMPLE DATA FIXTURES - DEAL
# ============================================================================

@pytest.fixture
def sample_deal_dict():
    """Sample deal data as dictionary"""
    return {
        'Id': str(uuid.uuid4()),
        'Title': 'Test Deal',
        'Description': 'This is a test deal for unit testing',
        'RegisterTime': datetime.now() - timedelta(days=30),
        'Price': Decimal('1000000'),
        'Status': 'در حال پیگیری',
        'PipelineStageId': 'stage-001',
        'PipelineId': 'pipeline-001',
        'ChangeToWonTime': None,
        'ChangeToLossTime': None,
        'LastTrackingTime': datetime.now() - timedelta(days=2),
        'NextTrackingTime': datetime.now() + timedelta(days=3),
        'ExpectedCloseDate': datetime.now() + timedelta(days=30),
        'LastActivityUpdateTime': datetime.now() - timedelta(days=1),
        'LastUpdateTime': datetime.now(),
        'Probability': 0.65,
        'ContactId': 'contact-001',
        'OwnerId': 'owner-001',
        'CreatorId': 'creator-001',
        'LabelId': 'label-001',
        'LostReason': '',
        'Source': 'CRM',
        'Currency': 'IRR',
        'ownerid': 'user-001',
        'updaterid': 'user-001',
        'sentiment_score': 0.8,
        'sentiment_label': 'مثبت'
    }


@pytest.fixture
def sample_deal(sample_deal_dict):
    """Sample Deal model instance"""
    return Deal.from_dict(sample_deal_dict)


@pytest.fixture
def sample_deals_list(sample_deal):
    """List of sample deals for portfolio testing"""
    deals = []
    statuses = ['در حال پیگیری', 'در حال مذاکره', 'پیش از توافق', 'درخواست شده']
    
    for i in range(10):
        deal_dict = {
            'Id': str(uuid.uuid4()),
            'Title': f'Deal {i+1}',
            'Description': f'Sample deal number {i+1}',
            'RegisterTime': datetime.now() - timedelta(days=30-i),
            'Price': Decimal(str(100000 + (i * 50000))),
            'Status': statuses[i % len(statuses)],
            'PipelineStageId': f'stage-{i:03d}',
            'PipelineId': 'pipeline-001',
            'ChangeToWonTime': None,
            'ChangeToLossTime': None,
            'LastTrackingTime': datetime.now() - timedelta(days=5-i),
            'NextTrackingTime': datetime.now() + timedelta(days=10+i),
            'ExpectedCloseDate': datetime.now() + timedelta(days=30+i),
            'LastActivityUpdateTime': datetime.now() - timedelta(days=3),
            'LastUpdateTime': datetime.now(),
            'Probability': 0.5 + (i * 0.05),
            'ContactId': f'contact-{i:03d}',
            'OwnerId': f'owner-{i:03d}',
            'CreatorId': 'creator-001',
            'LabelId': f'label-{i:03d}',
            'LostReason': '',
            'Source': 'CRM',
            'Currency': 'IRR',
            'ownerid': 'user-001',
            'updaterid': 'user-001',
            'sentiment_score': 0.7 + (i * 0.02),
            'sentiment_label': 'مثبت'
        }
        deals.append(Deal.from_dict(deal_dict))
    
    return deals


# ============================================================================
# SAMPLE DATA FIXTURES - ACTIVITY
# ============================================================================

@pytest.fixture
def sample_activity_dict(sample_deal):
    """Sample deal activity as dictionary"""
    return {
        'id': str(uuid.uuid4()),
        'dealid': sample_deal.Id,
        'title': 'Follow-up Call',
        'description': 'Customer follow-up call',
        'activitytype': 'تماس',
        'registerdate': datetime.now() - timedelta(days=5),
        'activitydate': datetime.now() - timedelta(days=5),
        'relatedto': 'deal',
        'related_to_id': sample_deal.Id,
        'direction': 'صادر',
        'ownerid': 'user-001',
        'participants': 'participant-001',
        'notes': 'Customer interested in product',
        'outcome': 'مثبت',
        'next_action': 'Send proposal',
        'due_date': datetime.now() + timedelta(days=7),
    }


@pytest.fixture
def sample_activity(sample_activity_dict):
    """Sample DealActivity model instance"""
    return DealActivity.from_dict(sample_activity_dict)


@pytest.fixture
def sample_activities_list(sample_deal):
    """List of sample activities"""
    activities = []
    activity_types = ['تماس', 'ایمیل', 'جلسه', 'نامه']
    outcomes = ['مثبت', 'منفی', 'خنثی']
    
    for i in range(10):
        activity_dict = {
            'id': str(uuid.uuid4()),
            'dealid': sample_deal.Id,
            'title': f'Activity {i+1}',
            'description': f'Sample activity number {i+1}',
            'activitytype': activity_types[i % len(activity_types)],
            'registerdate': datetime.now() - timedelta(days=20-i),
            'activitydate': datetime.now() - timedelta(days=20-i),
            'relatedto': 'deal',
            'related_to_id': sample_deal.Id,
            'direction': 'صادر',
            'ownerid': f'user-{i:03d}',
            'participants': f'participant-{i:03d}',
            'notes': f'Activity notes {i+1}',
            'outcome': outcomes[i % len(outcomes)],
            'next_action': 'Follow up',
            'due_date': datetime.now() + timedelta(days=5+i),
        }
        activities.append(DealActivity.from_dict(activity_dict))
    
    return activities


# ============================================================================
# SAMPLE DATA FIXTURES - AGENT
# ============================================================================

@pytest.fixture
def sample_agent_dict():
    """Sample CRM agent as dictionary"""
    return {
        'id': str(uuid.uuid4()),
        'groupowner': 'تیم فروش',
        'ownername': 'محمد علی',
        'adminid': 'admin-001',
        'role': 'فروشنده',
        'phone': '02112345678',
        'mobilephone': '09123456789',
        'personalid': '1234567890',
        'groupphone': '02187654321'
    }


@pytest.fixture
def sample_agent(sample_agent_dict):
    """Sample CRMAgent model instance"""
    return CRMAgent.from_dict(sample_agent_dict)


@pytest.fixture
def sample_agents_list():
    """List of sample CRM agents"""
    agents = []
    roles = ['فروشنده', 'مدیر فروش', 'متخصص', 'کارشناس']
    
    for i in range(8):
        agent_dict = {
            'id': str(uuid.uuid4()),
            'groupowner': 'تیم فروش',
            'ownername': f'Agent {i}',
            'adminid': 'admin-001',
            'role': roles[i % len(roles)],
            'phone': f'0211234567{i}',
            'mobilephone': f'0912345678{i}',
            'personalid': f'{1000000000 + i}',
            'groupphone': '02187654321'
        }
        agents.append(CRMAgent.from_dict(agent_dict))
    
    return agents


# ============================================================================
# SAMPLE DATA FIXTURES - SENTIMENT
# ============================================================================

@pytest.fixture
def sample_sentiment_dict(sample_deal, sample_activity):
    """Sample sentiment analysis as dictionary"""
    return {
        'id': str(uuid.uuid4()),
        'text': 'متن نمونه برای تحلیل احساس',
        'language': 'fa',
        'label': 'positive',
        'score': 0.95,
        'polarity': None,
        'subjectivity': None,
        'model_name': 'sentiment-model',
        'model_version': '1.0',
        'processed_at': datetime.now(),
        'deal_id': sample_deal.Id,
        'activity_id': sample_activity.id
    }


@pytest.fixture
def sample_sentiment(sample_sentiment_dict):
    """Sample SentimentAnalysis model instance"""
    return SentimentAnalysis.from_dict(sample_sentiment_dict)


# ============================================================================
# SERVICE INSTANCES (With mocked repositories)
# ============================================================================

@pytest.fixture
def deal_service(mock_repositories):
    """DealService instance with mocked repositories"""
    return DealService(mock_repositories)


@pytest.fixture
def sentiment_service(mock_repositories):
    """SentimentService instance with mocked repositories"""
    service = SentimentService(mock_repositories)
    service.model_loaded = False
    service.available = False
    return service


@pytest.fixture
def analytics_service(mock_repositories, sentiment_service):
    """AnalyticsService instance with mocked dependencies"""
    return AnalyticsService(mock_repositories, sentiment_service)


# ============================================================================
# UNIT TEST CONFIGURATION
# ============================================================================

@pytest.fixture(scope="function")
def unit_test_config():
    """Unit test specific configuration"""
    return {
        'use_mocks': True,
        'use_real_db': False,
        'timeout': 5,
        'verbose': False
    }


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    # Mocks
    'mock_db_manager',
    'mock_repositories',
    'mock_sentiment_service',
    'mock_cache_service',
    
    # Sample data
    'sample_deal_dict',
    'sample_deal',
    'sample_deals_list',
    'sample_activity_dict',
    'sample_activity',
    'sample_activities_list',
    'sample_agent_dict',
    'sample_agent',
    'sample_agents_list',
    'sample_sentiment_dict',
    'sample_sentiment',
    
    # Services
    'deal_service',
    'sentiment_service',
    'analytics_service',
    
    # Config
    'unit_test_config',
]