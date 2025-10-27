"""
tests/unit/conftest.py
----------------------
Unit test fixtures - Mocked services for isolated testing
"""
import pytest
import sys
import uuid
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, timedelta
from decimal import Decimal
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from models.deal_model import Deal, DealActivity, CRMAgent
from models.sentiment_model import SentimentAnalysis
from services.deal_service import DealService
from services.sentiment_service import SentimentService
from services.analytics_service import AnalyticsService


# ============================================================================
# MOCK DATABASE MANAGER - With realistic behavior
# ============================================================================

@pytest.fixture(scope="function")
def mock_db_manager():
    """Mock database manager with proper method implementations"""
    mock_db = Mock()
    
    # ========== Connection Pool ==========
    from psycopg2.pool import SimpleConnectionPool
    try:
        # Try to create real SimpleConnectionPool with dummy connection params
        mock_pool = SimpleConnectionPool(1, 5, 
            host='localhost', database='test', user='test', password='test')
    except Exception:
        # Fallback: Create Mock that passes isinstance check
        mock_pool = Mock(spec=SimpleConnectionPool)
        mock_pool.minconn = 1
        mock_pool.maxconn = 5
    mock_db.connection_pool = mock_pool
    
    # ========== Basic Operations ==========
    mock_db.test_connection = Mock(return_value=True)
    mock_db.close = Mock(return_value=None)
    
    # ========== Query Execution ==========
    def execute_query_impl(query, params=None):
        """Execute query - returns list or raises exception"""
        if not query or not isinstance(query, str):
            raise Exception("Invalid query")
        if "INVALID" in query:
            raise Exception("Syntax error in query")
        
        # Check for missing params when query has placeholders
        if '%s' in query and (params is None or len(params) == 0):
            raise Exception("Missing parameters for query")
        
        return []
    
    mock_db.execute_query = Mock(side_effect=execute_query_impl)
    
    # ========== Query Result Methods ==========
    mock_db.execute_insert = Mock(return_value='inserted-id-123')
    mock_db.execute_insert_batch = Mock(return_value=True)
    mock_db.execute_update = Mock(return_value=1)
    mock_db.execute_delete = Mock(return_value=1)
    
    # ========== Placeholder Conversion ==========
    def convert_placeholders(query):
        """Convert ? to %s for PostgreSQL"""
        if not isinstance(query, str):
            raise TypeError("Query must be string")
        return query.replace('?', '%s')
    
    mock_db._convert_query_placeholders = Mock(side_effect=convert_placeholders)
    
    # ========== Transaction Support ==========
    mock_db.begin_transaction = Mock(return_value=None)
    mock_db.commit = Mock(return_value=None)
    mock_db.rollback = Mock(return_value=None)
    
    # ========== Database Info ==========
    mock_db.get_database_stats = Mock(return_value={'tables': 5})
    mock_db.get_database_info = Mock(return_value={'current_database': 'test_db'})
    mock_db.get_table_info = Mock(return_value={'columns': 10})
    
    # ========== Backup ==========
    def create_backup_impl(path):
        """Create backup - raises exception for invalid paths"""
        if not path or '/invalid/' in path:
            raise Exception("Invalid backup path")
        return True
    
    mock_db.create_backup = Mock(side_effect=create_backup_impl)
    
    # ========== Context Manager Support ==========
    mock_db.__enter__ = Mock(return_value=mock_db)
    mock_db.__exit__ = Mock(return_value=False)
    
    return mock_db


# ============================================================================
# MOCK REPOSITORIES - Stateless for unit tests
# ============================================================================

@pytest.fixture(scope="function")
def mock_repositories():
    """Mock repository manager for unit tests"""
    repos = Mock()
    repos.deals = Mock()
    repos.activities = Mock()
    repos.agents = Mock()
    repos.sentiment = Mock()
    
    repos.__enter__ = Mock(return_value=repos)
    repos.__exit__ = Mock(return_value=False)
    
    return repos


# ============================================================================
# ALIAS FIXTURE - For compatibility with test_db_manager naming
# ============================================================================

@pytest.fixture(scope="function")
def test_db_manager(mock_db_manager):
    """Alias for unit tests - maps to mock_db_manager"""
    return mock_db_manager


# ============================================================================
# TEST REPOSITORIES ALIAS
# ============================================================================

@pytest.fixture(scope="function")
def test_repositories(mock_repositories):
    """Alias for unit tests - maps to mock_repositories"""
    return mock_repositories


# ============================================================================
# MOCK SERVICES
# ============================================================================

@pytest.fixture(scope="function")
def mock_sentiment_service():
    """Mock sentiment service for unit tests"""
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
    mock_service.analyze_activities_sentiment = Mock(return_value={
        "total_activities": 3,
        "analyzed_activities": 3,
        "sentiment_distribution": {}
    })
    mock_service.get_sentiment_trends = Mock(return_value={"trends": []})
    return mock_service


@pytest.fixture(scope="function")
def mock_cache_service():
    """Mock cache service for unit tests"""
    mock_cache = Mock()
    mock_cache.get = Mock(return_value=None)
    mock_cache.set = Mock(return_value=True)
    mock_cache.delete = Mock(return_value=True)
    mock_cache.clear = Mock(return_value=True)
    mock_cache.is_available = Mock(return_value=False)
    return mock_cache


# ============================================================================
# SERVICE FIXTURES
# ============================================================================

@pytest.fixture(scope="function")
def deal_service(mock_repositories):
    """Mock DealService instance"""
    service = Mock()
    service.get_deal = Mock(return_value={'Id': 'test-id', 'Title': 'Test Deal'})
    service.get_all_deals = Mock(return_value=[])
    service.create_deal = Mock(return_value='deal-id-123')
    service.update_deal = Mock(return_value=True)
    return service


@pytest.fixture(scope="function")
def sentiment_service(mock_repositories):
    """Mock SentimentService instance"""
    service = Mock()
    service.model_loaded = False
    service.available = False
    service.analyze_text = Mock(return_value={'sentiment': 'positive', 'confidence': 0.8})
    return service


@pytest.fixture(scope="function")
def analytics_service(mock_repositories):
    """Mock AnalyticsService instance"""
    service = Mock()
    service.analyze_deal_comprehensive = Mock(return_value={
        'health_score': 75,
        'risk_indicators': [],
        'recommendations': [],
        'insights': []
    })
    return service


# ============================================================================
# SAMPLE DATA FIXTURES
# ============================================================================

@pytest.fixture(scope="function")
def sample_deal_dict():
    """Sample deal data as dictionary"""
    return {
        'Id': str(uuid.uuid4()),
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
        'IsIdle': False,
        'IsRotten': False,
        'Fields': '{}',
        'Items': '[]',
        'MobilePhone': '+98912345678'
    }


@pytest.fixture(scope="function")
def sample_deal(sample_deal_dict):
    """Sample Deal model instance"""
    return Deal.from_dict(sample_deal_dict)


@pytest.fixture(scope="function")
def sample_activity_dict(sample_deal):
    """Sample deal activity as dictionary"""
    return {
        'id': str(uuid.uuid4()),
        'title': 'تماس تلفنی',
        'note': 'یادداشت فعالیت',
        'resultnote': 'نتیجه: موفق',
        'activitytypeid': 'call',
        'isdone': True,
        'duedate': datetime.now() - timedelta(days=5),
        'finishdate': datetime.now() - timedelta(days=5),
        'donedate': datetime.now() - timedelta(days=5),
        'registerdate': datetime.now() - timedelta(days=5),
        'lastupdatetime': datetime.now() - timedelta(days=5),
        'dealid': sample_deal.Id,
        'ownerid': 'user-001',
        'sentiment_score': 0.8,
        'sentiment_label': 'مثبت'
    }


@pytest.fixture(scope="function")
def sample_activity(sample_activity_dict):
    """Sample DealActivity model instance"""
    return DealActivity.from_dict(sample_activity_dict)


@pytest.fixture(scope="function")
def sample_activities_list(sample_deal):
    """List of sample activities for a deal"""
    activities = []
    activity_types = ['call', 'meeting', 'email', 'note']
    sentiments = ['مثبت', 'خنثی', 'منفی']
    
    for i in range(15):
        activity_dict = {
            'id': str(uuid.uuid4()),
            'title': f'فعالیت {i}',
            'note': f'یادداشت فعالیت شماره {i}',
            'resultnote': f'نتیجه: {"موفق" if i % 2 == 0 else "نیاز به پیگیری"}',
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


@pytest.fixture(scope="function")
def sample_deals_list():
    """List of sample deals"""
    deals = []
    statuses = ['در حال پیگیری', 'بسته شده برنده', 'بسته شده بازنده']
    
    for i in range(10):
        deal = Deal(
            Id=str(uuid.uuid4()),
            Title=f'سند فروش شماره {i+1}',
            Description=f'توضیح پروژه شماره {i+1}',
            RegisterTime=datetime.now() - timedelta(days=50-i*5),
            Price=Decimal(str(10000000 * (i+1))),
            Status=statuses[i % 3],
            PipelineStageId=f'stage-{i%5}',
            PipelineId='pipeline-001',
            ChangeToWonTime=datetime.now() - timedelta(days=5) if i % 3 == 1 else None,
            ChangeToLossTime=datetime.now() - timedelta(days=10) if i % 3 == 2 else None,
            LastTrackingTime=datetime.now() - timedelta(days=i),
            NextTrackingTime=datetime.now() + timedelta(days=i+5),
            ExpectedCloseDate=datetime.now() + timedelta(days=60-i*5),
            LastActivityUpdateTime=datetime.now() - timedelta(days=i+1),
            LastUpdateTime=datetime.now(),
            Probability=max(0.1, 0.8 - (i*0.05)),
            ContactId=f'contact-{i}',
            OwnerId=f'owner-{i%3}',
            CreatorId='creator-001',
            LabelId=f'label-{i%4}',
            LostReasonId=None,
            Pin=False,
            IsIdle=i % 5 == 0,
            IsRotten=i % 7 == 0,
            Fields='{}',
            Items='[]',
            MobilePhone=f'+9891234567{i}'
        )
        deals.append(deal)
    
    return deals


@pytest.fixture(scope="function")
def sample_agent_dict():
    """Sample CRM agent data as dictionary"""
    return {
        'id': str(uuid.uuid4()),
        'groupowner': 'تیم فروش',
        'ownername': 'علی احمدی',
        'adminid': 'admin-001',
        'role': 'Sales Manager',
        'phone': '+9851234567',
        'mobilephone': '+989123456789',
        'personalid': '1001234567',
        'groupphone': '+9851234500'
    }


@pytest.fixture(scope="function")
def sample_agent(sample_agent_dict):
    """Sample CRM Agent model instance"""
    return CRMAgent.from_dict(sample_agent_dict)


@pytest.fixture(scope="function")
def sample_agents_list():
    """List of sample agents"""
    agents = []
    agent_names = ['علی احمدی', 'فاطمه رضوی', 'حسن محمودی', 'مریم کریمی']
    
    for i, name in enumerate(agent_names):
        agent = CRMAgent(
            id=str(uuid.uuid4()),
            groupowner=f'تیم {i+1}',
            ownername=name,
            adminid=f'admin-{i}',
            role=['Sales Manager', 'Senior Executive', 'Coordinator', 'Analyst'][i],
            phone=f'+985{1000+i*100}',
            mobilephone=f'+98912345{600+i}',
            personalid=f'{1000+i}00000000',
            groupphone=f'+985{1200+i*100}'
        )
        agents.append(agent)
    
    return agents


@pytest.fixture(scope="function")
def sample_sentiment_dict():
    """Sample sentiment analysis data as dictionary"""
    return {
        'id': str(uuid.uuid4()),
        'activity_id': 'activity-001',
        'text': 'این یک متن مثبت است',
        'sentiment_label': 'مثبت',
        'confidence_score': 0.85,
        'model_version': '1.0'
    }


@pytest.fixture(scope="function")
def sample_sentiment(sample_sentiment_dict):
    """Sample SentimentAnalysis model instance"""
    return SentimentAnalysis.from_dict(sample_sentiment_dict)


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
    """Unit test specific configuration"""
    return {
        'mock_mode': True,
        'use_real_db': False,
        'sample_data_size': 'small'
    }


# ============================================================================
# CLEANUP
# ============================================================================

@pytest.fixture(scope="function", autouse=True)
def cleanup_after_test():
    """Cleanup after each test"""
    yield
    # Any cleanup code here