"""
tests/unit/conftest.py
----------------------
Unit test fixtures - Stateful mocked services for isolated testing
Implements in-memory storage to simulate database behavior
"""
import pytest
import sys
import uuid
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, timedelta
from decimal import Decimal
from dotenv import load_dotenv
from copy import deepcopy

# Load environment
load_dotenv()

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from models.deal_model import Deal, DealActivity, CRMAgent
from models.sentiment_model import SentimentAnalysis


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
        mock_pool = SimpleConnectionPool(1, 5, 
            host='localhost', database='test', user='test', password='test')
    except Exception:
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
# STATEFUL MOCK REPOSITORIES - With in-memory storage
# ============================================================================

@pytest.fixture(scope="function")
def mock_repositories():
    """Mock repository manager with stateful in-memory storage"""
    repos = Mock()
    
    # ========== In-Memory Storage ==========
    repos._deals_store = {}
    repos._activities_store = {}
    repos._agents_store = {}
    repos._sentiment_store = {}
    
    # ========== DEAL REPOSITORY MOCKS ==========
    
    def create_deal(deal):
        """Create deal and store it"""
        repos._deals_store[deal.Id] = deepcopy(deal)
        return deal.Id
    
    def get_deal_by_id(deal_id):
        """Get deal by ID - returns None if not found"""
        return repos._deals_store.get(deal_id)
    
    def get_all_deals():
        """Get all deals"""
        return list(repos._deals_store.values())
    
    def update_deal(deal):
        """Update existing deal"""
        if deal.Id in repos._deals_store:
            repos._deals_store[deal.Id] = deepcopy(deal)
            return True
        return False
    
    def delete_deal(deal_id):
        """Delete deal by ID"""
        if deal_id in repos._deals_store:
            del repos._deals_store[deal_id]
            return True
        return False
    
    def get_deals_by_status(status):
        """Get deals filtered by status"""
        return [d for d in repos._deals_store.values() if d.Status == status]
    
    def get_deals_statistics():
        """Get deal statistics"""
        deals = list(repos._deals_store.values())
        by_status = {}
        for deal in deals:
            by_status[deal.Status] = by_status.get(deal.Status, 0) + 1
        return {
            'total_deals': len(deals),
            'by_status': by_status
        }
    
    repos.deals = Mock()
    repos.deals.create_deal = Mock(side_effect=create_deal)
    repos.deals.get_deal_by_id = Mock(side_effect=get_deal_by_id)
    repos.deals.get_all_deals = Mock(side_effect=get_all_deals)
    repos.deals.update_deal = Mock(side_effect=update_deal)
    repos.deals.delete_deal = Mock(side_effect=delete_deal)
    repos.deals.get_deals_by_status = Mock(side_effect=get_deals_by_status)
    repos.deals.get_deals_statistics = Mock(side_effect=get_deals_statistics)
    
    # ========== ACTIVITY REPOSITORY MOCKS ==========
    
    def create_activity(activity):
        """Create activity and store it"""
        repos._activities_store[activity.id] = deepcopy(activity)
        return activity.id
    
    def get_activity_by_id(activity_id):
        """Get activity by ID - returns None if not found"""
        return repos._activities_store.get(activity_id)
    
    def get_all_activities():
        """Get all activities"""
        return list(repos._activities_store.values())
    
    def get_activities_by_deal(deal_id):
        """Get activities for a specific deal"""
        return [a for a in repos._activities_store.values() if a.dealid == deal_id]
    
    def update_activity_sentiment(activity_id, sentiment_score, sentiment_label):
        """Update activity sentiment"""
        if activity_id in repos._activities_store:
            activity = repos._activities_store[activity_id]
            activity.sentiment_score = sentiment_score
            activity.sentiment_label = sentiment_label
            return True
        return False
    
    def get_pending_activities():
        """Get activities that are not done"""
        return [a for a in repos._activities_store.values() if not a.isdone]
    
    repos.activities = Mock()
    repos.activities.create_activity = Mock(side_effect=create_activity)
    repos.activities.get_activity_by_id = Mock(side_effect=get_activity_by_id)
    repos.activities.get_all_activities = Mock(side_effect=get_all_activities)
    repos.activities.get_activities_by_deal = Mock(side_effect=get_activities_by_deal)
    repos.activities.update_activity_sentiment = Mock(side_effect=update_activity_sentiment)
    repos.activities.get_pending_activities = Mock(side_effect=get_pending_activities)
    
    # ========== AGENT REPOSITORY MOCKS ==========
    
    def create_agent(agent):
        """Create agent and store it"""
        repos._agents_store[agent.id] = deepcopy(agent)
        return agent.id
    
    def get_agent_by_id(agent_id):
        """Get agent by ID - returns None if not found"""
        return repos._agents_store.get(agent_id)
    
    def get_all_agents():
        """Get all agents"""
        return list(repos._agents_store.values())
    
    def get_agents_by_role(role):
        """Get agents filtered by role"""
        return [a for a in repos._agents_store.values() if a.role == role]
    
    def update_agent(agent):
        """Update existing agent"""
        if agent.id in repos._agents_store:
            repos._agents_store[agent.id] = deepcopy(agent)
            return True
        return False
    
    repos.agents = Mock()
    repos.agents.create_agent = Mock(side_effect=create_agent)
    repos.agents.get_agent_by_id = Mock(side_effect=get_agent_by_id)
    repos.agents.get_all_agents = Mock(side_effect=get_all_agents)
    repos.agents.get_agents_by_role = Mock(side_effect=get_agents_by_role)
    repos.agents.update_agent = Mock(side_effect=update_agent)
    
    # ========== SENTIMENT REPOSITORY MOCKS ==========
    
    def save_sentiment(sentiment):
        """Save sentiment analysis"""
        repos._sentiment_store[sentiment.id] = deepcopy(sentiment)
        return sentiment.id
    
    def get_sentiments_by_deal(deal_id):
        """Get sentiments for a deal"""
        return [s for s in repos._sentiment_store.values() if hasattr(s, 'deal_id') and s.deal_id == deal_id]
    
    repos.sentiment = Mock()
    repos.sentiment.save_sentiment = Mock(side_effect=save_sentiment)
    repos.sentiment.get_sentiments_by_deal = Mock(side_effect=get_sentiments_by_deal)
    
    # ========== Context Manager Support ==========
    repos.__enter__ = Mock(return_value=repos)
    repos.__exit__ = Mock(return_value=False)
    repos.close = Mock(return_value=None)
    
    return repos


# ============================================================================
# ALIAS FIXTURES - For compatibility
# ============================================================================

@pytest.fixture(scope="function")
def test_db_manager(mock_db_manager):
    """Alias for unit tests - maps to mock_db_manager"""
    return mock_db_manager


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
    
    def analyze_text_impl(text):
        """Analyze text sentiment"""
        if not text or text.strip() == '':
            return {'error': 'Empty text', 'sentiment': 'خنثی'}
        return {
            "sentiment": "positive",
            "confidence": 0.85,
            "text_preview": text[:50]
        }
    
    def analyze_batch_impl(texts):
        """Analyze batch of texts"""
        if not texts or len(texts) == 0:
            return []
        return [
            {"sentiment": "positive", "confidence": 0.85},
            {"sentiment": "negative", "confidence": 0.75},
            {"sentiment": "neutral", "confidence": 0.65}
        ][:len(texts)]
    
    mock_service.analyze_text = Mock(side_effect=analyze_text_impl)
    mock_service.analyze_batch = Mock(side_effect=analyze_batch_impl)
    mock_service.analyze_activities_sentiment = Mock(return_value={
        "total_activities": 3,
        "analyzed_activities": 3,
        "sentiment_distribution": {
            "positive": 1,
            "neutral": 1,
            "negative": 1
        }
    })
    mock_service.get_sentiment_trends = Mock(return_value={"trends": []})
    mock_service.get_cache_stats = Mock(return_value={"cached": 0, "total": 0})
    mock_service.clear_cache = Mock(return_value={"cleared": 0})
    
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
    """Mock DealService instance with proper behavior"""
    service = Mock()
    
    def get_deal(deal_id):
        """Get deal - returns dict or None"""
        deal = mock_repositories.deals.get_deal_by_id(deal_id)
        return deal.to_dict() if deal else None
    
    def get_all_deals():
        """Get all deals"""
        deals = mock_repositories.deals.get_all_deals()
        return [d.to_dict() for d in deals]
    
    def get_deals_by_status(status):
        """Get deals by status"""
        deals = mock_repositories.deals.get_deals_by_status(status)
        return [d.to_dict() for d in deals]
    
    def get_deals_summary(days=30):
        """Get deals summary"""
        return {
            'total_deals': len(mock_repositories.deals.get_all_deals()),
            'active_deals': len([d for d in mock_repositories.deals.get_all_deals() if d.Status == 'در حال پیگیری']),
            'closed_deals': len([d for d in mock_repositories.deals.get_all_deals() if d.Status != 'در حال پیگیری']),
            'total_value': sum(d.Price or 0 for d in mock_repositories.deals.get_all_deals())
        }
    
    def get_deal_timeline(deal_id):
        """Get deal timeline"""
        deal = mock_repositories.deals.get_deal_by_id(deal_id)
        if not deal:
            return {'error': 'Deal not found'}
        activities = mock_repositories.activities.get_activities_by_deal(deal_id)
        return {
            'timeline': [{'id': a.id, 'title': a.title} for a in activities],
            'total_events': len(activities)
        }
    
    service.get_deal = Mock(side_effect=get_deal)
    service.get_all_deals = Mock(side_effect=get_all_deals)
    service.get_deals_by_status = Mock(side_effect=get_deals_by_status)
    service.get_deals_summary = Mock(side_effect=get_deals_summary)
    service.get_deal_timeline = Mock(side_effect=get_deal_timeline)
    service._calculate_deal_duration = Mock(return_value=30)
    
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
    service.get_portfolio_overview = Mock(return_value={'total_value': 0})
    service.invalidate_deal_cache = Mock(return_value=None)
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
    statuses = ['Pending', 'Won', 'Lost']
    
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
        'label': 'positive',
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