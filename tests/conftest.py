"""
tests/conftest.py
-----------------
Shared pytest fixtures with graceful service availability handling
"""
import uuid
import pytest
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock
from decimal import Decimal
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

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
# SERVICE AVAILABILITY DETECTION
# ============================================================================

def check_database_available():
    """Check if PostgreSQL is available"""
    try:
        from database.database import DatabaseManager
        db = DatabaseManager()
        result = db.test_connection()
        db.close()
        print("✅ Database available")
        return result
    except Exception as e:
        print(f"⚠️  Database unavailable: {type(e).__name__}")
        return False


def check_redis_available():
    """Check if Redis is available"""
    try:
        import redis
        host = os.getenv('REDIS_HOST', 'localhost')
        port = int(os.getenv('REDIS_PORT', 6379))
        r = redis.Redis(
            host=host, 
            port=port, 
            socket_connect_timeout=2,
            socket_timeout=2
        )
        r.ping()
        print("✅ Redis available")
        return True
    except Exception as e:
        print(f"⚠️  Redis unavailable: {type(e).__name__}")
        return False


def check_chromadb_available():
    """Check if ChromaDB is available"""
    try:
        import chromadb
        from config.rag_settings import RAGSettings
        RAGSettings.validate_paths()
        client = chromadb.PersistentClient(path=str(RAGSettings.CHROMA_DB_DIR))
        print("✅ ChromaDB available")
        return True
    except Exception as e:
        print(f"⚠️  ChromaDB unavailable: {type(e).__name__}")
        return False


# Cache availability status
_service_status = {
    'database': None,
    'redis': None,
    'chromadb': None
}

def get_service_status(service_name: str) -> bool:
    """Get cached service availability status"""
    if _service_status[service_name] is None:
        if service_name == 'database':
            _service_status[service_name] = check_database_available()
        elif service_name == 'redis':
            _service_status[service_name] = check_redis_available()
        elif service_name == 'chromadb':
            _service_status[service_name] = check_chromadb_available()
    return _service_status[service_name]


# ============================================================================
# DATABASE FIXTURES - WITH GRACEFUL FALLBACK
# ============================================================================

@pytest.fixture(scope="session")
def test_db_manager():
    """Create database manager (real or mock based on availability)"""
    if get_service_status('database'):
        try:
            db = create_database_manager()
            yield db
            db.close()
            return
        except Exception:
            pass
    
    # Fallback to mock
    print("📦 Using MOCK database")
    mock_db = Mock()
    mock_db.execute_query = Mock(return_value=[])
    mock_db.execute_insert = Mock(return_value=1)
    mock_db.execute_update = Mock(return_value=1)
    mock_db.execute_delete = Mock(return_value=1)
    mock_db.test_connection = Mock(return_value=True)
    mock_db.close = Mock()
    yield mock_db


@pytest.fixture(scope="function")
def test_repositories(test_db_manager):
    """Create fresh repositories for each test"""
    try:
        return create_repositories(test_db_manager)
    except Exception:
        # Return mock repositories if creation fails
        repos = Mock()
        repos.deals = Mock()
        repos.activities = Mock()
        repos.agents = Mock()
        repos.sentiment = Mock()
        repos.__enter__ = Mock(return_value=repos)
        repos.__exit__ = Mock(return_value=False)
        return repos


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
    service.model_loaded = False
    service.available = False
    return service


@pytest.fixture(scope="function")
def analytics_service(test_repositories, sentiment_service):
    """Create AnalyticsService instance"""
    return AnalyticsService(test_repositories, sentiment_service)


@pytest.fixture(scope="function")
def mock_sentiment_service():
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


# ============================================================================
# CACHE SERVICE FIXTURES
# ============================================================================

@pytest.fixture(scope="function")
def cache_service():
    """Create cache service (real or mock based on availability)"""
    if get_service_status('redis'):
        try:
            from services.cache_service import CacheService
            return CacheService()
        except Exception:
            pass
    
    # Fallback to mock
    print("📦 Using MOCK cache")
    mock_cache = Mock()
    mock_cache.get = Mock(return_value=None)
    mock_cache.set = Mock(return_value=True)
    mock_cache.delete = Mock(return_value=True)
    mock_cache.clear = Mock(return_value=True)
    mock_cache.is_available = Mock(return_value=False)
    return mock_cache


# ============================================================================
# CHROMADB FIXTURES
# ============================================================================

@pytest.fixture(scope="function")
def vector_store():
    """Create vector store (real or mock based on availability)"""
    if get_service_status('chromadb'):
        try:
            from services.vector_store_service import VectorStoreService
            service = VectorStoreService()
            import asyncio
            asyncio.run(service.initialize())
            yield service
            return
        except Exception:
            pass
    
    # Fallback to mock
    print("📦 Using MOCK vector store")
    mock_store = Mock()
    mock_store.search = Mock(return_value=[])
    mock_store.add = Mock(return_value=True)
    mock_store.delete = Mock(return_value=True)
    yield mock_store


# ============================================================================
# DATA FIXTURES - DEALS
# ============================================================================

@pytest.fixture
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
def sample_activity_dict(sample_deal):
    """Sample deal activity as dictionary"""
    return {
        'id': str(uuid.uuid4()),
        'title': 'تماس تلفنی',  # Persian: Phone Call
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
            'id': str(uuid.uuid4()),
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
            'role': roles[i % 4],
            'phone': f'0211234567{i}',
            'mobilephone': f'0912345678{i}',
            'personalid': f'{1000000000 + i}',
            'groupphone': '02187654321'
        }
        agents.append(CRMAgent.from_dict(agent_dict))
    
    return agents


# ============================================================================
# SENTIMENT FIXTURES
# ============================================================================

@pytest.fixture
def sample_sentiment_dict(sample_deal, sample_activity):
    """Sample sentiment analysis as dictionary"""
    return {
        'id': str(uuid.uuid4()),
        'text': 'متن نمونه برای تحلیل احساس',
        'language': 'fa',
        'label': 'positive',  # Must be: positive, negative, or neutral (English)
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
# SCENARIO FIXTURES - DEALS WITH ACTIVITIES
# ============================================================================

@pytest.fixture
def sample_deals_list(sample_deal):
    """List of sample deals for portfolio testing"""
    deals = []
    deal_statuses = ['در حال پیگیری', 'در حال مذاکره', 'پیش از توافق', 'درخواست شده']
    
    for i in range(10):
        deal_dict = {
            'Id': str(uuid.uuid4()),
            'Title': f'Test Deal {i}',
            'Description': f'Deal number {i}',
            'RegisterTime': datetime.now() - timedelta(days=30+i),
            'Price': Decimal(str(1000000 * (i+1))),
            'Status': deal_statuses[i % 4],
            'PipelineStageId': f'stage-{i%3}',
            'PipelineId': 'pipeline-001',
            'LastTrackingTime': datetime.now() - timedelta(days=2+i),
            'Probability': 0.5 + (i % 5) * 0.1,
            'ContactId': f'contact-{i}',
            'OwnerId': f'owner-{i%3}',
            'CreatorId': 'creator-001',
            'sentiment_score': 0.6 + (i % 4) * 0.1,
            'sentiment_label': 'مثبت' if i % 2 == 0 else 'خنثی'
        }
        deals.append(Deal.from_dict(deal_dict))
    
    return deals


@pytest.fixture
def healthy_deal_scenario(sample_deal, sample_activities_list):
    """Scenario: Healthy deal with recent positive activities"""
    deal = sample_deal
    deal.Status = 'در حال مذاکره'
    deal.Probability = 0.85
    deal.LastTrackingTime = datetime.now() - timedelta(days=1)
    deal.sentiment_score = 0.9
    deal.sentiment_label = 'مثبت'
    
    # Make activities recent and positive
    activities = []
    for i, activity in enumerate(sample_activities_list[:5]):
        activity.registerdate = datetime.now() - timedelta(days=i)
        activity.isdone = True
        activity.sentiment_label = 'مثبت'
        activity.sentiment_score = 0.85 + (i % 2) * 0.05
        activities.append(activity)
    
    return {
        'deal': deal,
        'activities': activities
    }


@pytest.fixture
def at_risk_deal_scenario(sample_deal, sample_activities_list):
    """Scenario: Deal at risk with stale activities and negative sentiment"""
    deal = sample_deal
    deal.Status = 'در حال پیگیری'
    deal.Probability = 0.2
    deal.LastTrackingTime = datetime.now() - timedelta(days=25)
    deal.RegisterTime = datetime.now() - timedelta(days=90)
    deal.sentiment_score = 0.3
    deal.sentiment_label = 'منفی'
    
    # Make activities old and negative
    activities = []
    for i, activity in enumerate(sample_activities_list[:5]):
        activity.registerdate = datetime.now() - timedelta(days=20+i)
        activity.isdone = False
        activity.sentiment_label = 'منفی' if i % 2 == 0 else 'خنثی'
        activity.sentiment_score = 0.3 - (i * 0.05)
        activities.append(activity)
    
    return {
        'deal': deal,
        'activities': activities
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
    config.addinivalue_line(
        "markers", "requires_redis: marks tests that require Redis"
    )
    config.addinivalue_line(
        "markers", "requires_chromadb: marks tests that require ChromaDB"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection"""
    for item in items:
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)