"""
tests/conftest.py
-----------------
Shared pytest fixtures for all tests
"""

import pytest
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock
from decimal import Decimal

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from database.database import create_database_manager
from models.repositories import create_repositories
from models.deal_model import Deal, DealActivity, CRMAgent
from models.sentiment_model import SentimentAnalysis
from services.deal_service import DealService
from services.sentiment_service import SentimentService
from services.analytics_service import AnalyticsService


# ============================================================================
# DATABASE FIXTURES
# ============================================================================

@pytest.fixture(scope="session")
def test_db_manager():
    """Create database manager for testing (session scope)"""
    db = create_database_manager()
    yield db
    db.close()


@pytest.fixture(scope="function")
def test_repositories(test_db_manager):
    """Create fresh repositories for each test"""
    return create_repositories(test_db_manager)


@pytest.fixture(scope="function")
def mock_db_manager():
    """Mock database manager for unit tests"""
    mock_db = Mock()
    mock_db.execute_query = Mock(return_value=[])
    mock_db.execute_insert = Mock(return_value=1)
    mock_db.execute_update = Mock(return_value=1)
    mock_db.execute_delete = Mock(return_value=1)
    mock_db.test_connection = Mock(return_value=True)
    return mock_db


# ============================================================================
# SERVICE FIXTURES
# ============================================================================

@pytest.fixture(scope="function")
def deal_service(test_repositories):
    """Create DealService instance"""
    return DealService(test_repositories)


@pytest.fixture(scope="function")
def sentiment_service(test_repositories):
    """Create SentimentService instance"""
    service = SentimentService(test_repositories)
    # Don't actually load the model in tests
    service.model_loaded = False
    service.available = False
    return service


@pytest.fixture(scope="function")
def analytics_service(test_repositories, sentiment_service):
    """Create AnalyticsService instance"""
    return AnalyticsService(test_repositories, sentiment_service)


@pytest.fixture(scope="function")
def mock_sentiment_service():
    """Mock sentiment service for unit tests"""
    mock_service = Mock()
    mock_service.model_loaded = True
    mock_service.available = True
    mock_service.analyze_text = Mock(return_value={
        "sentiment": "مثبت",
        "confidence": 0.85,
        "text_preview": "Sample text..."
    })
    return mock_service


# ============================================================================
# DATA FIXTURES - DEALS
# ============================================================================

@pytest.fixture
def sample_deal_dict():
    """Sample deal data as dictionary"""
    return {
        'Id': 'test-deal-001',
        'Title': 'Test Deal',
        'Description': 'This is a test deal',
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
        'LostReasonId': None,
        'Pin': False,
        'LostReasonNote': '',
        'LostReasonOther': '',
        'Feedback': '',
        'IsIdle': False,
        'IsRotten': False,
        'IsRottenInStage': False,
        'Fields': '{}',
        'Items': '[]',
        'MobilePhone': '09123456789'
    }


@pytest.fixture
def sample_deal(sample_deal_dict):
    """Sample Deal model instance"""
    return Deal.from_dict(sample_deal_dict)


@pytest.fixture
def sample_deals_list():
    """List of sample deals"""
    deals = []
    statuses = ['در حال پیگیری', 'مذاکره', 'بسته شده']
    
    for i in range(10):
        deal_dict = {
            'Id': f'deal-{i:03d}',
            'Title': f'معامله تست {i}',
            'Description': f'توضیحات معامله شماره {i}',
            'RegisterTime': datetime.now() - timedelta(days=60-i*5),
            'Price': Decimal(str(1000000 + i * 100000)),
            'Status': statuses[i % 3],
            'PipelineStageId': f'stage-{i%3:03d}',
            'PipelineId': 'pipeline-001',
            'ContactId': f'contact-{i:03d}',
            'Probability': 0.5 + (i * 0.05),
            'LastTrackingTime': datetime.now() - timedelta(days=i),
            'LastUpdateTime': datetime.now() - timedelta(days=i//2),
        }
        deals.append(Deal.from_dict(deal_dict))
    
    return deals


# ============================================================================
# DATA FIXTURES - ACTIVITIES
# ============================================================================

@pytest.fixture
def sample_activity_dict():
    """Sample activity data as dictionary"""
    return {
        'id': 'activity-001',
        'title': 'تماس تلفنی',
        'note': 'تماس با مشتری برای پیگیری پیشنهاد',
        'resultnote': 'مشتری علاقه‌مند است',
        'activitytypeid': 'type-call',
        'isprivate': False,
        'isdone': True,
        'ispinned': False,
        'duedate': datetime.now() - timedelta(days=1),
        'finishdate': datetime.now(),
        'donedate': datetime.now(),
        'registerdate': datetime.now() - timedelta(days=2),
        'lastupdatetime': datetime.now(),
        'dealid': 'test-deal-001',
        'creatorid': 'user-001',
        'ownerid': 'user-001',
        'updaterid': 'user-001',
        'sentiment_score': 0.8,
        'sentiment_label': 'مثبت'
    }


@pytest.fixture
def sample_activity(sample_activity_dict):
    """Sample DealActivity model instance"""
    return DealActivity.from_dict(sample_activity_dict)


@pytest.fixture
def sample_activities_list(sample_deal):
    """List of sample activities for a deal"""
    activities = []
    activity_types = ['call', 'meeting', 'email', 'note']
    sentiments = ['مثبت', 'خنثی', 'منفی']
    
    for i in range(15):
        activity_dict = {
            'id': f'activity-{i:03d}',
            'title': f'فعالیت {i}',
            'note': f'یادداشت فعالیت شماره {i}',
            'resultnote': f'نتیجه: موفق' if i % 2 == 0 else 'نتیجه: نیاز به پیگیری',
            'activitytypeid': activity_types[i % 4],
            'isdone': i % 3 != 0,
            'duedate': datetime.now() - timedelta(days=20-i),
            'finishdate': datetime.now() - timedelta(days=20-i) if i % 3 != 0 else None,
            'donedate': datetime.now() - timedelta(days=20-i) if i % 3 != 0 else None,
            'registerdate': datetime.now() - timedelta(days=25-i),
            'lastupdatetime': datetime.now() - timedelta(days=18-i),
            'dealid': sample_deal.Id,
            'ownerid': 'user-001',
            'sentiment_score': 0.5 + (i % 3) * 0.2,
            'sentiment_label': sentiments[i % 3]
        }
        activities.append(DealActivity.from_dict(activity_dict))
    
    return activities


# ============================================================================
# DATA FIXTURES - AGENTS
# ============================================================================

@pytest.fixture
def sample_agent_dict():
    """Sample CRM agent data as dictionary"""
    return {
        'id': 'agent-001',
        'groupowner': 'تیم فروش',
        'ownername': 'علی احمدی',
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
    """List of sample agents"""
    agents = []
    roles = ['فروشنده', 'مدیر فروش', 'پشتیبانی']
    
    for i in range(5):
        agent_dict = {
            'id': f'agent-{i:03d}',
            'groupowner': f'تیم {i}',
            'ownername': f'کاربر {i}',
            'adminid': 'admin-001',
            'role': roles[i % 3],
            'phone': f'021123456{i:02d}',
            'mobilephone': f'0912345678{i}',
            'personalid': f'123456789{i}',
            'groupphone': f'021876543{i:02d}'
        }
        agents.append(CRMAgent.from_dict(agent_dict))
    
    return agents


# ============================================================================
# DATA FIXTURES - SENTIMENT
# ============================================================================

@pytest.fixture
def sample_sentiment_dict():
    """Sample sentiment analysis data"""
    return {
        'id': 1,
        'text': 'مشتری بسیار راضی بود و قصد خرید دارد',
        'language': 'fa',
        'label': 'مثبت',
        'score': 0.92,
        'polarity': 0.8,
        'subjectivity': 0.6,
        'model_name': 'HooshvareLab/bert-fa-base-uncased',
        'model_version': '1.0',
        'processed_at': datetime.now(),
        'deal_id': 'test-deal-001',
        'activity_id': 'activity-001'
    }


@pytest.fixture
def sample_sentiment(sample_sentiment_dict):
    """Sample SentimentAnalysis model instance"""
    return SentimentAnalysis.from_dict(sample_sentiment_dict)


# ============================================================================
# SCENARIO FIXTURES
# ============================================================================

@pytest.fixture
def healthy_deal_scenario(sample_deal, sample_activities_list):
    """Scenario: Healthy deal with recent positive activities"""
    # Modify deal to be healthy
    sample_deal.LastTrackingTime = datetime.now() - timedelta(days=1)
    sample_deal.Status = 'در حال پیگیری'
    
    # Make activities recent and positive
    for i, activity in enumerate(sample_activities_list[:5]):
        activity.registerdate = datetime.now() - timedelta(days=i+1)
        activity.sentiment_label = 'مثبت'
        activity.sentiment_score = 0.8 + (i * 0.02)
    
    return {
        'deal': sample_deal,
        'activities': sample_activities_list[:5]
    }


@pytest.fixture
def at_risk_deal_scenario(sample_deal, sample_activities_list):
    """Scenario: Deal at risk with stale activities"""
    # Modify deal to be at risk
    sample_deal.LastTrackingTime = datetime.now() - timedelta(days=20)
    sample_deal.RegisterTime = datetime.now() - timedelta(days=90)
    sample_deal.Status = 'در حال پیگیری'
    
    # Make activities old and some negative
    for i, activity in enumerate(sample_activities_list[:3]):
        activity.registerdate = datetime.now() - timedelta(days=20+i)
        activity.sentiment_label = 'منفی' if i % 2 == 0 else 'خنثی'
        activity.sentiment_score = 0.3 - (i * 0.05)
    
    return {
        'deal': sample_deal,
        'activities': sample_activities_list[:3]
    }


# ============================================================================
# MOCK FIXTURES
# ============================================================================

@pytest.fixture
def mock_repositories():
    """Mock repository manager for unit tests"""
    repos = Mock()
    repos.deals = Mock()
    repos.activities = Mock()
    repos.agents = Mock()
    repos.sentiment = Mock()
    
    # Setup context manager
    repos.__enter__ = Mock(return_value=repos)
    repos.__exit__ = Mock(return_value=False)
    
    return repos


# ============================================================================
# CONFIGURATION FIXTURES
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


# ============================================================================
# CLEANUP FIXTURES
# ============================================================================

@pytest.fixture(scope="function", autouse=True)
def cleanup_after_test():
    """Cleanup after each test"""
    yield
    # Add cleanup code here if needed
    # e.g., clear caches, reset mocks, etc.


# ============================================================================
# PYTEST CONFIGURATION
# ============================================================================

def pytest_configure(config):
    """Configure pytest"""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )
    config.addinivalue_line(
        "markers", "requires_db: marks tests that require database connection"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection"""
    # Add markers automatically based on test location
    for item in items:
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)